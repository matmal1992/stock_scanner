import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

from PySide6.QtCore import QThread

from config.app_config import load_config
from src.stock_scanner.core.paths import get_log_file_path
from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository, NewsEntry
from src.stock_scanner.workers.worker_status import WorkerStatus

logger = logging.getLogger(__name__)

# https://api.telegram.org/bot<chat_token>/getUpdates
# https://api.telegram.org/bot<TWOJ_TOKEN>/getChat?chat_id=<CHAT_ID>

config = load_config()
alert_chat_token = config.get("alert_chat_token")
state_chat_token = config.get("state_chat_token")
debug_chat_token = config.get("debug_chat_token")

alert_chat_id = config.get("alert_chat_id")
state_chat_id = config.get("state_chat_id")
debug_chat_id = config.get("debug_chat_id")

state_chat_pinned_message_id = config.get("state_chat_pinned_message_id")
llm_pinned_error_msg_id = config.get("llm_pinned_error_msg_id")
llm_pinned_error_screen_msg_id = config.get("llm_pinned_error_screen_msg_id")
llm_error_log_file_id = config.get("llm_error_log_file_id")


def _execute_request(request: urllib.request.Request, timeout: int) -> dict | None:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))

        if result.get("ok"):
            return result

        logger.error("Telegram API error: %s", result)

    except urllib.error.HTTPError as exc:
        logger.error(
            "Telegram HTTP error: status=%s, response=%s",
            exc.code,
            exc.read().decode("utf-8", errors="replace"),
        )
    return None


class TelegramCommandWorker(QThread):
    def __init__(self) -> None:
        super().__init__()
        self._running = True
        self._offset: int | None = None

    def _request(self, method: str, payload: dict) -> dict | None:
        url = f"https://api.telegram.org/bot{alert_chat_token}/{method}"
        data = urllib.parse.urlencode(payload).encode("utf-8")
        request = urllib.request.Request(url, data=data)

        result = _execute_request(request, timeout=10)

        return result

    def _send_logs(self) -> None:
        url = f"https://api.telegram.org/bot{alert_chat_token}/sendDocument"
        boundary = "----TelegramBoundaryLog"

        try:
            log_file_path = get_log_file_path()

            with open(log_file_path, "rb") as log_file:
                file_bytes = log_file.read()

            body = (
                (
                    f"--{boundary}\r\n"
                    f'Content-Disposition: form-data; name="chat_id"\r\n\r\n'
                    f"{alert_chat_id}\r\n"
                    f"--{boundary}\r\n"
                    f'Content-Disposition: form-data; name="caption"\r\n\r\n'
                    f"\r\n"
                    f"--{boundary}\r\n"
                    f'Content-Disposition: form-data; name="document"; filename="logs.txt"\r\n'
                    f"Content-Type: text/plain\r\n\r\n"
                ).encode("utf-8")
                + file_bytes
                + f"\r\n--{boundary}--\r\n".encode("utf-8")
            )

            request = urllib.request.Request(
                url,
                data=body,
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
                method="POST",
            )

            with urllib.request.urlopen(request, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))

            if not result.get("ok"):
                logger.error(f"Telegram API error: {result}")

        except Exception as e:
            logger.exception(f"Błąd wysyłania pliku logu: {e}")

    def run(self) -> None:
        logger.info("Telegram command worker started")

        while self._running:
            payload = {
                "timeout": 5,
                "allowed_updates": json.dumps(["message"]),
            }

            if self._offset is not None:
                payload["offset"] = self._offset

            result = self._request("getUpdates", payload)

            if result is None:
                self.msleep(1000)
                continue

            for update in result.get("result", []):
                self._offset = update["update_id"] + 1

                message = update.get("message", {})
                chat = message.get("chat", {})

                if str(chat.get("id")) != debug_chat_id:
                    continue

                text = message.get("text", "")
                if not isinstance(text, str):
                    continue

                if text.strip().lower() == "logs":
                    logger.info("Received Telegram test command")
                    self._send_logs()

        logger.info("Telegram command worker stopped")

    def stop(self) -> None:
        self._running = False


class TelegramStateBot:
    def __init__(self) -> None:
        self.last_text: str = "No app state text"
        self.last_error_text: str = "No error text"
        self.last_screen: bytes = b""
        self.last_error_log: str = "No log"

    def _request(self, method: str, payload: dict, chat_token: str) -> dict | None:
        url = f"https://api.telegram.org/bot{chat_token}/{method}"
        data = urllib.parse.urlencode(payload).encode("utf-8")
        request = urllib.request.Request(url, data=data)
        result = _execute_request(request, timeout=10)

        return result

    def update_app_state(self, text: str) -> None:
        if text == self.last_text:
            return

        chat_token = str(state_chat_token)

        result = self._request(
            "editMessageText",
            {
                "chat_id": state_chat_id,
                "message_id": state_chat_pinned_message_id,
                "text": text,
            },
            chat_token,
        )

        if result is not None:
            self.last_text = text

    def update_llm_error_status(self, error_status_text: str) -> None:
        if error_status_text == self.last_error_text:
            print("error status bez zmian")
            return

        chat_token = str(debug_chat_token)

        result = self._request(
            "editMessageText",
            {
                "chat_id": debug_chat_id,
                "message_id": llm_pinned_error_msg_id,
                "text": error_status_text,
            },
            chat_token,
        )

        if result is not None:
            self.last_error_text = error_status_text

    def update_llm_status_screen(self, image: bytes) -> None:
        if image == self.last_screen:
            return

        url = f"https://api.telegram.org/bot{debug_chat_token}/editMessageMedia"

        boundary = "----TelegramBoundary"
        media = json.dumps({"type": "photo", "media": "attach://photo"})

        body = (
            (
                f"--{boundary}\r\n"
                'Content-Disposition: form-data; name="chat_id"\r\n\r\n'
                f"{debug_chat_id}\r\n"
                f"--{boundary}\r\n"
                'Content-Disposition: form-data; name="message_id"\r\n\r\n'
                f"{llm_pinned_error_screen_msg_id}\r\n"
                f"--{boundary}\r\n"
                'Content-Disposition: form-data; name="media"\r\n\r\n'
                f"{media}\r\n"
                f"--{boundary}\r\n"
                'Content-Disposition: form-data; name="photo"; filename="llm.png"\r\n'
                "Content-Type: image/png\r\n\r\n"
            ).encode("utf-8")
            + image
            + (f"\r\n--{boundary}--\r\n").encode("utf-8")
        )

        request = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))

            if result.get("ok"):
                self.last_screen = image
            else:
                logger.error(
                    "Telegram editMessageMedia error: %s",
                    result,
                )

        except Exception:
            logger.exception("Nie udało się zaktualizować screenshotu na Telegram")

    def update_log_file(self, log_content: str) -> None:
        if log_content == self.last_error_log:
            return

        url = f"https://api.telegram.org/bot{debug_chat_token}/editMessageMedia"
        boundary = "----TelegramBoundaryLogUpdate"

        file_bytes = log_content.encode("utf-8")

        media_json = json.dumps(
            {
                "type": "document",
                "media": "attach://error_log.txt",
                "caption": "",
            }
        )

        body = (
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="chat_id"\r\n\r\n'
                f"{debug_chat_id}\r\n"
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="message_id"\r\n\r\n'
                f"{llm_error_log_file_id}\r\n"
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="media"\r\n\r\n'
                f"{media_json}\r\n"
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="error_log.txt"; filename="error_log.txt"\r\n'
                f"Content-Type: text/plain\r\n\r\n"
            ).encode("utf-8")
            + file_bytes
            + f"\r\n--{boundary}--\r\n".encode("utf-8")
        )

        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))

                if result.get("ok"):
                    self.last_error_log = log_content
                else:
                    logger.error("Telegram editMessageMedia error: %s", result)

        except Exception:
            logger.exception("Nie udało się zaktualizować log file na Telegram")


class TelegramStateWorker(QThread):
    def __init__(self, entry_repo: EntryRepository) -> None:
        super().__init__()
        self.entry_repo = entry_repo

        self.bot = TelegramStateBot()
        self._running = True

    def run(self) -> None:
        while self._running:
            try:
                last_update = datetime.now().strftime("%H:%M:%S")
                app_status_text = WorkerStatus.format_message(last_update)
                llm_error_text = WorkerStatus._llm_error
                llm_error_screen = WorkerStatus._llm_error_screen
                llm_full_error_log = WorkerStatus._llm_full_error_log

                self.bot.update_app_state(app_status_text)
                self.bot.update_llm_error_status(llm_error_text)
                self.bot.update_llm_status_screen(llm_error_screen)
                self.bot.update_log_file(llm_full_error_log)

            except Exception as exc:
                logger.exception(f"Błąd aktualizacji Scanner State: {exc}")

            for _ in range(50):
                if not self._running:
                    break
                self.msleep(100)

    def stop(self) -> None:
        logger.info("Stop telegram worker called")
        self._running = False


class TelegramBot:
    telegram_state_worker: TelegramStateWorker
    command_worker: TelegramCommandWorker

    @classmethod
    def init(cls, entry_repo: EntryRepository) -> None:
        cls.telegram_state_worker = TelegramStateWorker(entry_repo)
        cls.telegram_state_worker.start()
        cls.command_worker = TelegramCommandWorker()
        cls.command_worker.start()

    @classmethod
    def send_alert(cls, entry: NewsEntry) -> None:
        message = cls.build_alert(entry)

        if message is None:
            return

        cls.send_message(message)

    @classmethod
    def build_alert(cls, entry: NewsEntry) -> str | None:
        forecast = entry["llm"]
        title = entry["title"]
        published = entry["published"]
        source = entry["source_type"]
        url = entry["link"]
        justification = entry["justification"]

        if published is None:
            return None

        published = published[11:]

        if forecast in {"Wzrost", "Silny wzrost"}:
            forecast_display = f"🟩 {forecast}"
        elif forecast in {"Spadek", "Silny spadek"}:
            forecast_display = f"🟥 {forecast}"
        elif forecast == "Neutralny":
            forecast_display = f"⬜ {forecast}"
        else:
            forecast_display = forecast

        return f'<a href="{url}">{source}</a> | {published}\n{title}\n{forecast_display} - {justification}'

    @classmethod
    def send_message(cls, text: str) -> None:
        url = f"https://api.telegram.org/bot{alert_chat_token}/sendMessage"
        payload = {
            "chat_id": alert_chat_id,
            "text": text,
            "parse_mode": "HTML",
            "link_preview_options": json.dumps({"is_disabled": True}),
        }

        request = urllib.request.Request(
            url,
            data=urllib.parse.urlencode(payload).encode("utf-8"),
            method="POST",
        )

        result = _execute_request(request, timeout=10)

        if not result:
            pass

    @classmethod
    def stop_telegram(cls) -> None:
        if cls.telegram_state_worker.isRunning():
            cls.telegram_state_worker.stop()
            cls.telegram_state_worker.wait()

        if cls.command_worker.isRunning():
            cls.command_worker.stop()
            cls.command_worker.wait()


# zostawić tylko wzrost i silny wzrost. Wyjatek to tracked_tickers
# add to tracked tickers - wpisz ticker, a będzie on dodany do bazy
# detekcja braku internetu - info po przywróceniu połączenia

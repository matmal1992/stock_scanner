import json
import logging
import urllib.parse
import urllib.request

from PySide6.QtCore import QThread

from config.app_config import load_config
from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository, NewsEntry

logger = logging.getLogger(__name__)

config = load_config()
telegram_token = config.get("telegram_bot_token")
telegram_chat_id = config.get("telegram_chat_id")


class TelegramCommandWorker(QThread):
    def __init__(self, token: str | None, chat_id: str | None) -> None:
        super().__init__()
        self.token = token
        self.chat_id = str(chat_id)
        self._running = True
        self._offset: int | None = None

    def _request(self, method: str, payload: dict) -> dict | None:
        url = f"https://api.telegram.org/bot{self.token}/{method}"
        data = urllib.parse.urlencode(payload).encode("utf-8")
        request = urllib.request.Request(url, data=data)

        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))

            if result.get("ok"):
                return result

            logger.error("Telegram command API error: %s", result)

        except Exception:
            if self._running:
                logger.exception("Telegram command HTTP error")

        return None

    def _send_reply(self, text: str) -> None:
        self._request(
            "sendMessage",
            {
                "chat_id": self.chat_id,
                "text": text,
            },
        )

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

                # Obsługuj wyłącznie wiadomości z wybranego czatu.
                if str(chat.get("id")) != self.chat_id:
                    continue

                text = message.get("text", "")
                if not isinstance(text, str):
                    continue

                if text.strip().lower() == "test":
                    logger.info("Received Telegram test command")
                    self._send_reply("test command received")

        logger.info("Telegram command worker stopped")

    def stop(self) -> None:
        self._running = False


class TelegramStateBot:
    def __init__(self) -> None:
        config = load_config()
        self.token = config.get("telegram_state_bot_token")
        self.chat_id = config.get("telegram_state_chat_id")
        self.message_id = config.get("telegram_state_pinned_message_id")
        self.last_text: str | None = None

    def _request(self, method: str, payload: dict) -> dict | None:
        url = f"https://api.telegram.org/bot{self.token}/{method}"
        data = urllib.parse.urlencode(payload).encode("utf-8")
        request = urllib.request.Request(url, data=data)

        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))

            if result.get("ok"):
                return result

            logger.error("State bot API error: %s", result)
        except Exception:
            logger.exception("State bot HTTP error")

        return None

    def update(self, text: str) -> None:
        if not self.token or not self.chat_id or not self.message_id:
            logger.info("No token")
            return

        if text == self.last_text:
            return

        result = self._request(
            "editMessageText",
            {
                "chat_id": self.chat_id,
                "message_id": self.message_id,
                "text": text,
            },
        )

        if result is not None:
            self.last_text = text


class TelegramStateWorker(QThread):
    def __init__(self, entry_repo: EntryRepository) -> None:
        super().__init__()
        self.entry_repo = entry_repo
        self.bot = TelegramStateBot()
        self._running = True

    def run(self) -> None:
        while self._running:
            logger.info("Telegram worker running")
            try:
                pending = self.entry_repo.get_pending_number()
                logger.info(f"Pending number: {pending}")
                self.bot.update(f"Pending: {pending}")
            except Exception:
                logger.exception("Błąd aktualizacji Scanner State")

            for _ in range(50):
                if not self._running:
                    break
                self.msleep(100)

    def stop(self) -> None:
        logger.info("Stop telegram worker called")
        self._running = False


class TelegramBot:
    entry_repo: EntryRepository | None = None
    alert_chat_token: str | None = None
    state_chat_token: str | None = None
    alert_chat_id: str | None = None
    state_chat_id: str | None = None
    telegram_state_worker: TelegramStateWorker
    command_worker: TelegramCommandWorker

    @classmethod
    def init(cls, entry_repo: EntryRepository) -> None:
        config = load_config()
        cls.alert_chat_token = config.get("telegram_bot_token")
        cls.state_chat_token = config.get("telegram_state_bot_token")
        cls.alert_chat_id = config.get("telegram_chat_id")
        cls.state_chat_id = config.get("telegram_state_chat_id")
        cls.telegram_state_worker = TelegramStateWorker(entry_repo)
        cls.telegram_state_worker.start()
        cls.command_worker = TelegramCommandWorker(cls.state_chat_token, cls.state_chat_id)
        cls.command_worker.start()

        cls.entry_repo = entry_repo

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
    def send_message(self, text: str) -> None:
        if not self.alert_chat_token or not self.alert_chat_id:
            logger.warning("Telegram nie jest skonfigurowany.")
            return

        url = f"https://api.telegram.org/bot{self.alert_chat_token}/sendMessage"
        payload = {
            "chat_id": self.alert_chat_id,
            "text": text,
            "parse_mode": "HTML",
            "link_preview_options": json.dumps({"is_disabled": True}),
        }

        request = urllib.request.Request(
            url,
            data=urllib.parse.urlencode(payload).encode("utf-8"),
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))

            if not result.get("ok"):
                logger.error("Telegram API error: %s", result)

        except Exception:
            logger.exception("Nie udało się wysłać wiadomości Telegram.")


# diagnostyka: stan aplikacji: ilosc pending, finished, skipped, wszystkich, errorow
# screeny z exceptionow
# stan workerow
# data i godzina ostatniego scrapowania espi, ostatniego przetworzenia LLM
# exception w formie traceback
# osobny kanał dla alertów, osobny dla logów, osobny dla debugowania
# sterowanie aplikacją przez telegram: start/stop scrapowania, start/stop LLM, restart Gemini, aplikacji
# zostawić tylko wzrost i silny wzrost. Wyjatek to tracked_tickers
# add to tracked tickers - wpisz ticker, a będzie on dodany do bazy
# alert, że jeśli jest pending, a llm nie running.
# detekcja braku internetu - info po przywróceniu połączenia

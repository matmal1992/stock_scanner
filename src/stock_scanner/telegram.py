import json
import logging
import time
import urllib.parse
import urllib.request

from PySide6.QtCore import QObject, QThread, Signal

from config.app_config import load_config
from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository, NewsEntry
from src.stock_scanner.strategies.news_tracker.gpw_worker import GPWService
from src.stock_scanner.strategies.news_tracker.llm_worker import LLMService

logger = logging.getLogger(__name__)

config = load_config()
telegram_token = config.get("telegram_bot_token")
telegram_chat_id = config.get("telegram_chat_id")


class TelegramClient:
    def _request(self, method: str, payload: dict) -> dict | None:
        url = f"https://api.telegram.org/bot{telegram_token}/{method}"

        data = urllib.parse.urlencode(payload).encode("utf-8")
        request = urllib.request.Request(url, data=data, method="POST")

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read().decode("utf-8")

            result = json.loads(body)

            if result.get("ok"):
                return result

            logger.error("Telegram API error: %s", result)

        except Exception as e:
            logger.error("Telegram HTTP error: %s", e)

        return None

    def send_message(self, text: str) -> None:
        payload = {
            "chat_id": telegram_chat_id,
            "text": text,
            "parse_mode": "HTML",
            "link_preview_options": json.dumps({"is_disabled": True}),
        }

        self._request("sendMessage", payload)


class TelegramService:
    client = TelegramClient()

    def __init__(self) -> None:
        self.listener = TelegramBotListener()

    def start(self) -> None:
        self.listener.start()
        self.send_alert("🟢 Stock Scanner uruchomiony.")

    def stop(self) -> None:
        self.listener.stop()

        if self.listener.isRunning():
            self.listener.wait()

    @classmethod
    def send_alert(cls, text: str) -> None:
        cls.client.send_message(text)

    @classmethod
    def send_message(cls, entry: NewsEntry) -> None:
        message = cls.build_message(entry)

        if message is None:
            return

        cls.client.send_message(message)

    @classmethod
    def build_message(cls, entry: NewsEntry) -> str | None:
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

        return f'{published} | <a href="{url}">{source}</a>\n{title}\n{forecast_display} - {justification}'


class TelegramBotListener(QThread):
    command_received = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._running = True
        self._last_update_id = 0
        self.telegram_client = TelegramClient()

    def run(self) -> None:
        logger.info("Uruchomiono nasłuchiwanie Telegram Bot...")
        while self._running:
            try:
                updates = self._get_updates()
                for update in updates:
                    self._last_update_id = update["update_id"]
                    self._process_update(update)
            except Exception as e:
                logger.error("Błąd podczas odpytywania Telegrama: %s", e)
                time.sleep(3)

    def stop(self) -> None:
        self._running = False

    def _get_updates(self) -> list:
        url = f"https://api.telegram.org/bot{telegram_token}/getUpdates"
        params = {"offset": self._last_update_id + 1, "timeout": 30}
        query_string = urllib.parse.urlencode(params)
        full_url = f"{url}?{query_string}"

        req = urllib.request.Request(full_url)

        with urllib.request.urlopen(req, timeout=25) as response:
            data = json.loads(response.read().decode("utf-8"))

        if data.get("ok"):
            return data.get("result", [])

        return []

    def _process_update(self, update: dict) -> None:
        message = update.get("message")
        if not message:
            return

        chat_id = str(message.get("chat", {}).get("id"))
        text = message.get("text", "").strip().lower()

        if chat_id != telegram_chat_id:
            logger.warning("Odrzucono wiadomość od nieznanego czatu: %s", chat_id)
            return

        self.command_received.emit(text)

    def send_response(self, text: str) -> None:
        self.telegram_client.send_message(text)


class ApplicationController(QObject):
    response_ready = Signal(str)

    def __init__(
        self,
        entry_repo: EntryRepository,
        gpw_service: GPWService,
        llm_service: LLMService,
    ) -> None:
        super().__init__()

        self.entry_repo = entry_repo
        self.gpw_service = gpw_service
        self.llm_service = llm_service

    def handle_command(self, command: str) -> None:
        logger.info("Telegram command: %s", command)

        if command == "status":
            self.response_ready.emit(self.get_status())
        else:
            logger.warning("Nieznana komenda: %s", command)

    def get_status(self) -> str:
        gpw = self.gpw_service.is_running()
        llm = self.llm_service.is_running()
        pending = self.entry_repo.get_pending_number()

        return (
            "Status aplikacji\n\n"
            f"GPW: {'🟢 aktywny' if gpw else '🔴 zatrzymany'}\n"
            f"LLM: {'🟢 aktywny' if llm else '🔴 zatrzymany'}\n"
            f"Pending: {pending}\n"
        )


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

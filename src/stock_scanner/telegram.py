import json
import logging
import urllib.parse
import urllib.request
from typing import ClassVar

from config.app_config import load_config
from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository, NewsEntry

logger = logging.getLogger(__name__)

config = load_config()
telegram_token = config.get("telegram_bot_token")
telegram_chat_id = config.get("telegram_chat_id")


# class TelegramClient:
#     def __init__(self) -> None:
#         self._pending_message_id: int | None = None
#         self._pending_message_text: str | None = None

#     def _request(self, method: str, payload: dict) -> dict | None:
#         url = f"https://api.telegram.org/bot{telegram_token}/{method}"

#         data = urllib.parse.urlencode(payload).encode("utf-8")
#         request = urllib.request.Request(url, data=data, method="POST")

#         try:
#             with urllib.request.urlopen(request, timeout=30) as response:
#                 body = response.read().decode("utf-8")

#             result = json.loads(body)

#             if result.get("ok"):
#                 return result

#             logger.error("Telegram API error: %s", result)

#         except Exception as e:
#             logger.error("Telegram HTTP error: %s", e)

#         return None

#     def send_message(self, text: str) -> int | None:
#         payload = {
#             "chat_id": telegram_chat_id,
#             "text": text,
#             "parse_mode": "HTML",
#             "link_preview_options": json.dumps({"is_disabled": True}),
#         }

#         result = self._request("sendMessage", payload)
#         if result is None:
#             return None

#         return result["result"]["message_id"]

#     def update_pending_message(self, pending: int) -> None:
#         text = f"Pending: {pending}"

#         if self._pending_message_id is None:
#             chat = self._request("getChat", {"chat_id": telegram_chat_id})
#             pinned_message = (chat or {}).get("result", {}).get("pinned_message", {})
#             pinned_text = pinned_message.get("text", "")
#             sent_by_bot = pinned_message.get("from", {}).get("is_bot", False)

#             if sent_by_bot and pinned_text.startswith("Pending: "):
#                 self._pending_message_id = pinned_message["message_id"]
#                 self._pending_message_text = pinned_text

#         if self._pending_message_id is not None:
#             if self._pending_message_text == text:
#                 return

#             result = self._request(
#                 "editMessageText",
#                 {
#                     "chat_id": telegram_chat_id,
#                     "message_id": self._pending_message_id,
#                     "text": text,
#                 },
#             )
#             if result is not None:
#                 self._pending_message_text = text
#             return

#         message_id = self.send_message(text)
#         if message_id is None:
#             return

#         self._pending_message_id = message_id
#         self._pending_message_text = text
#         self._request(
#             "pinChatMessage",
#             {
#                 "chat_id": telegram_chat_id,
#                 "message_id": message_id,
#                 "disable_notification": True,
#             },
#         )


# class TelegramService:
#     client = TelegramClient()

#     def __init__(self) -> None:
#         self.listener = TelegramBotListener()

#     def start(self, pending_count_provider: Callable[[], int] | None = None) -> None:
#         self.listener.pending_count_provider = pending_count_provider
#         self.listener.start()
#         self.send_alert("🟢 Stock Scanner uruchomiony.")

#     def stop(self) -> None:
#         self.listener.stop()

#         if self.listener.isRunning():
#             self.listener.wait()

#     @classmethod
#     def send_alert(cls, text: str) -> None:
#         cls.client.send_message(text)

#     @classmethod
#     def send_message(cls, entry: NewsEntry) -> None:
#         message = cls.build_message(entry)

#         if message is None:
#             return

#         cls.client.send_message(message)

#     @classmethod
#     def build_message(cls, entry: NewsEntry) -> str | None:
#         forecast = entry["llm"]
#         title = entry["title"]
#         published = entry["published"]
#         source = entry["source_type"]
#         url = entry["link"]
#         justification = entry["justification"]

#         if published is None:
#             return None

#         published = published[11:]

#         if forecast in {"Wzrost", "Silny wzrost"}:
#             forecast_display = f"🟩 {forecast}"
#         elif forecast in {"Spadek", "Silny spadek"}:
#             forecast_display = f"🟥 {forecast}"
#         elif forecast == "Neutralny":
#             forecast_display = f"⬜ {forecast}"
#         else:
#             forecast_display = forecast

#         return f'{published} | <a href="{url}">{source}</a>\n{title}\n{forecast_display} - {justification}'


# class TelegramBotListener(QThread):
#     command_received = Signal(str)

#     def __init__(self) -> None:
#         super().__init__()
#         self._running = True
#         self._last_update_id = 0
#         self.telegram_client = TelegramClient()
#         self.pending_count_provider: Callable[[], int] | None = None
#         self._last_pending_refresh = 0.0

#     def run(self) -> None:
#         logger.info("Uruchomiono nasłuchiwanie Telegram Bot...")
#         while self._running:
#             self._refresh_pending_message()
#             try:
#                 updates = self._get_updates()
#                 for update in updates:
#                     self._last_update_id = update["update_id"]
#                     self._process_update(update)
#             except Exception as e:
#                 logger.error("Błąd podczas odpytywania Telegrama: %s", e)
#                 time.sleep(3)

#     def _refresh_pending_message(self) -> None:
#         if self.pending_count_provider is None:
#             return

#         now = time.monotonic()
#         if now - self._last_pending_refresh < 30:
#             return

#         self._last_pending_refresh = now
#         try:
#             pending = self.pending_count_provider()
#             self.telegram_client.update_pending_message(pending)
#         except Exception:
#             logger.exception("Nie udało się odświeżyć licznika pending na Telegramie")

#     def stop(self) -> None:
#         self._running = False

#     def _get_updates(self) -> list:
#         url = f"https://api.telegram.org/bot{telegram_token}/getUpdates"
#         params = {"offset": self._last_update_id + 1, "timeout": 30}
#         query_string = urllib.parse.urlencode(params)
#         full_url = f"{url}?{query_string}"

#         req = urllib.request.Request(full_url)

#         with urllib.request.urlopen(req, timeout=35) as response:
#             data = json.loads(response.read().decode("utf-8"))

#         if data.get("ok"):
#             return data.get("result", [])

#         return []

#     def _process_update(self, update: dict) -> None:
#         message = update.get("message")
#         if not message:
#             return

#         chat_id = str(message.get("chat", {}).get("id"))
#         text = message.get("text", "").strip().lower()

#         if chat_id != telegram_chat_id:
#             logger.warning("Odrzucono wiadomość od nieznanego czatu: %s", chat_id)
#             return

#         self.command_received.emit(text)

#     def send_response(self, text: str) -> None:
#         self.telegram_client.send_message(text)


# class ApplicationController(QObject):
#     response_ready = Signal(str)

#     def __init__(
#         self,
#         entry_repo: EntryRepository,
#         gpw_service: GPWService,
#         llm_service: LLMService,
#     ) -> None:
#         super().__init__()

#         self.entry_repo = entry_repo
#         self.gpw_service = gpw_service
#         self.llm_service = llm_service

#     def handle_command(self, command: str) -> None:
#         logger.info("Telegram command: %s", command)

#         if command == "status":
#             self.response_ready.emit(self.get_status())
#         else:
#             logger.warning("Nieznana komenda: %s", command)

#     def get_status(self) -> str:
#         gpw = self.gpw_service.is_running()
#         llm = self.llm_service.is_running()
#         total = self.entry_repo.get_total_number()
#         pending = self.entry_repo.get_pending_number()

#         return (
#             "Status aplikacji\n\n"
#             f"GPW: {'🟢 aktywny' if gpw else '🔴 zatrzymany'}\n"
#             f"LLM: {'🟢 aktywny' if llm else '🔴 zatrzymany'}\n"
#             f"Wpisy w bazie: {total}\n"
#             f"Pending: {pending}\n"
#         )


# class TelegramStateBot:
#     def __init__(self) -> None:
#         self.token = config.get("telegram_state_bot_token")
#         self.chat_id = config.get("telegram_state_chat_id")
#         self.message_id: int | None = None
#         self.last_text: str | None = None

#     def _request(self, method: str, payload: dict) -> dict | None:
#         url = f"https://api.telegram.org/bot{self.token}/{method}"
#         data = urllib.parse.urlencode(payload).encode("utf-8")
#         request = urllib.request.Request(url, data=data)

#         try:
#             with urllib.request.urlopen(request, timeout=10) as response:
#                 result = json.loads(response.read().decode("utf-8"))

#             if result.get("ok"):
#                 return result

#             logger.error("State bot API error: %s", result)
#         except Exception:
#             logger.exception("State bot HTTP error")

#         return None

#     def update(self, text: str) -> None:
#         if not self.token or not self.chat_id:
#             return

#         if text == self.last_text:
#             return

#         if self.message_id is not None:
#             result = self._request(
#                 "editMessageText",
#                 {
#                     "chat_id": self.chat_id,
#                     "message_id": self.message_id,
#                     "text": text,
#                 },
#             )

#             if result is not None:
#                 self.last_text = text
#                 return

#             # Jeśli edycja się nie powiedzie, spróbuj utworzyć wiadomość.
#             self.message_id = None

#         result = self._request(
#             "sendMessage",
#             {
#                 "chat_id": self.chat_id,
#                 "text": text,
#             },
#         )

#         if result is not None:
#             self.message_id = result["result"]["message_id"]
#             self.last_text = text

#             self._request(
#                 "pinChatMessage",
#                 {
#                     "chat_id": self.chat_id,
#                     "message_id": self.message_id,
#                     "disable_notification": True,
#                 },
#             )


# class TelegramStateWorker(QThread):
#     def __init__(self, entry_repo: EntryRepository) -> None:
#         super().__init__()
#         self.entry_repo = entry_repo
#         self.bot = TelegramStateBot()
#         self._running = True

#     def run(self) -> None:
#         while self._running:
#             try:
#                 pending = self.entry_repo.get_pending_number()
#                 self.bot.update(f"Pending: {pending}")
#             except Exception:
#                 logger.exception("Błąd aktualizacji Scanner State")

#             for _ in range(50):
#                 if not self._running:
#                     break
#                 self.msleep(100)

#     def stop(self) -> None:
#         self._running = False


class Telegram:
    client: ClassVar["TelegramClient | None"] = None
    entry_repo: ClassVar[EntryRepository | None] = None

    @classmethod
    def init(cls, entry_repo: EntryRepository) -> None:
        if cls.client is not None:
            return

        config = load_config()
        token = config.get("telegram_bot_token")
        chat_id = config.get("telegram_chat_id")

        cls.entry_repo = entry_repo
        cls.client = TelegramClient(token, chat_id)

    @classmethod
    def send_alert(cls, text: str) -> None:
        if cls.client is not None:
            cls.client.send_message(text)

    @classmethod
    def send_message(cls, entry: NewsEntry) -> None:
        message = cls.build_message(entry)

        if message is None:
            return

        if cls.client is not None:
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

        return f'<a href="{url}">{source}</a> | {published}\n{title}\n{forecast_display} - {justification}'


class TelegramClient:
    def __init__(self, token: str | None, chat_id: str | None) -> None:
        self.token = token
        self.chat_id = chat_id

    def send_message(self, text: str) -> None:
        if not self.token or not self.chat_id:
            logger.warning("Telegram nie jest skonfigurowany.")
            return

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
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

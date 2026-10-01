import json
import logging
import time
import urllib.parse
import urllib.request

from PySide6.QtCore import QThread, Signal

from config.app_config import load_config
from src.stock_scanner.core.utils import get_actual_time
from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository, NewsEntry
from src.stock_scanner.strategies.news_tracker.gpw_worker import GPWService
from src.stock_scanner.strategies.news_tracker.llm_worker import LLMService

logger = logging.getLogger(__name__)

config = load_config()
telegram_token = config.get("telegram_bot_token")
telegram_chat_id = config.get("telegram_chat_id")

ALERT_FORECASTS = {"Wzrost", "Silny wzrost"}

# diagnostyka: stan aplikacji: ilosc pending, finished, skipped, wszystkich, errorow
# screeny z exceptionow
# stan workerow
# data i godzina ostatniego scrapowania espi, ostatniego przetworzenia LLM
# exception w formie traceback
# osobny kanał dla alertów, osobny dla logów, osobny dla debugowania
# sterowanie aplikacją przez telegram: start/stop scrapowania, start/stop LLM, restart Gemini, aplikacji
# zostawić tylko wzrost i silny wzrost. Wyjatek to tracked_tickers


class TelegramBotListener(QThread):
    # Sygnały do komunikacji z głównym wątkiem/aplikacją jeśli chcesz wykonywać akcje
    command_received = Signal(str)

    def __init__(
        self,
        token: str,
        allowed_chat_id: str,
        entry_repo: EntryRepository,
        gpw_service: GPWService,
        llm_service: LLMService,
    ) -> None:
        super().__init__()
        self.token = token
        self.allowed_chat_id = str(allowed_chat_id)
        self.entry_repo = entry_repo
        self.gpw_service = gpw_service
        self.llm_service = llm_service
        self._running = True
        self._last_update_id = 0

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
        url = f"https://api.telegram.org/bot{self.token}/getUpdates"
        params = {
            "offset": self._last_update_id + 1,
            "timeout": 10,  # Long polling timeout w sekundach
        }
        query_string = urllib.parse.urlencode(params)
        full_url = f"{url}?{query_string}"

        req = urllib.request.Request(full_url)
        # Timeout po stronie socketu ustawiamy nieco wyżej niż timeout w API
        with urllib.request.urlopen(req, timeout=15) as response:
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

        # BEZPIECZEŃSTWO: Obsługuj tylko wiadomości z Twojego chat_id!
        if chat_id != self.allowed_chat_id:
            logger.warning("Odrzucono wiadomość od nieznanego czatu: %s", chat_id)
            return

        self._handle_command(text)

    def _handle_command(self, cmd: str) -> None:
        if cmd in ["state", "/state", "stan"]:
            self._reply_state()
        elif cmd in ["restart_llm", "/restart_llm"]:
            self._reply("Restartowanie usługi LLM...")
            # np. self.llm_service.wake() lub reset
        elif cmd in ["help", "/start", "/help"]:
            self._reply("Dostępne komendy:\n- state\n- restart_llm")
        else:
            self._reply(f"Nieznana komenda: {cmd}")

    def _reply_state(self) -> None:
        # Pobieramy statystyki z bazy danych
        # has_pending = self.entry_repo.has_pending()

        # Przykład pobrania z bazy zliczeń (warto dodać taką metodę do EntryRepository)
        # np. stats = self.entry_repo.get_stats()

        # Wpisy w stanie 'pending'
        pending_entry = self.entry_repo.get_last_pending()
        pending_status = "Tak (są w kolejce)" if pending_entry else "Brak (0)"

        msg = (
            "📊 **Stan aplikacji:**\n\n"
            f"• Czy są oczekujące LLM: **{pending_status}**\n"
            f"• Wątek GPW: **{'Aktywny' if self.gpw_service.is_running() else 'Bezczynny'}**\n"
            f"• Wątek LLM: **{'Aktywny' if self.llm_service.is_running() else 'Bezczynny'}**\n"
        )
        self._reply(msg)

    def _reply(self, text: str) -> None:
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.allowed_chat_id,
            "text": text,
            "parse_mode": "HTML",
        }
        data = urllib.parse.urlencode(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        try:
            urllib.request.urlopen(req, timeout=10)
        except Exception as e:
            logger.error("Błąd wysyłania odpowiedzi na Telegram: %s", e)


def build_message(entry: NewsEntry) -> str | None:
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


def send_telegram_message(entry: NewsEntry) -> bool:
    message = build_message(entry)

    if message is None:
        return False

    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"

    payload = {
        "chat_id": telegram_chat_id,
        "text": message,
        "parse_mode": "HTML",
        "link_preview_options": json.dumps({"is_disabled": True}),
    }

    data = urllib.parse.urlencode(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST")

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8")

        result = json.loads(body)
        return bool(result.get("ok", False))
    except Exception as e:
        logger.error(f"{get_actual_time()} - TELEGRAM ERROR: {type(e)}, {e}")
        return False


def send_telegram_alert(alert: str) -> bool:
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"

    payload = {"chat_id": telegram_chat_id, "text": alert}

    data = urllib.parse.urlencode(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST")

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8")

        result = json.loads(body)
        return bool(result.get("ok", False))
    except Exception as e:
        logger.error(f"{get_actual_time()} -TELEGRAM ERROR: {type(e)}, {e}")
        return False

import json
import logging
import urllib.parse
import urllib.request

from src.stock_scanner.download.config import load_config
from src.stock_scanner.strategies.news_tracker.entry_repo import NewsRow

logger = logging.getLogger(__name__)

config = load_config()
telegram_token = config.get("telegram_bot_token")
telegram_chat_id = config.get("telegram_chat_id")

ALERT_FORECASTS = {"Wzrost", "Silny wzrost"}


def build_message(entry: NewsRow) -> str | None:
    forecast = entry["llm"]

    if forecast not in ALERT_FORECASTS:
        return None

    ticker = entry["ticker"]

    if not ticker:
        logger.warning("Brak tickera dla entry %s", entry["id"])
        return None

    return f"{ticker}: {forecast}"


def send_telegram_message(entry: NewsRow) -> bool:
    message = build_message(entry)

    if message is None:
        return False

    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"

    payload = {"chat_id": telegram_chat_id, "text": message}

    data = urllib.parse.urlencode(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST")

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8")

        logger.info("TELEGRAM RESPONSE: %s", body)

        result = json.loads(body)
        return bool(result.get("ok", False))
    except Exception as e:
        logger.error(f"TELEGRAM ERROR: {type(e)}, {e}")
        return False

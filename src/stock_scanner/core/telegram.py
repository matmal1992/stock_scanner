import json
import logging
import urllib.parse
import urllib.request

from config.app_config import load_config
from src.stock_scanner.core.utils import get_actual_time
from src.stock_scanner.strategies.news_tracker.entry_repo import NewsEntry

logger = logging.getLogger(__name__)

config = load_config()
telegram_token = config.get("telegram_bot_token")
telegram_chat_id = config.get("telegram_chat_id")

ALERT_FORECASTS = {"Wzrost", "Silny wzrost"}


def build_message(entry: NewsEntry) -> str | None:
    # forecast = entry["llm"]
    title = entry["title"]
    published = entry["published"]
    source = entry["source_type"]
    url = entry["link"]

    if published is None:
        return None

    published = published[11:]

    ticker = entry["ticker"]

    return f'{published} | <a href="{url}">{source}</a>\n{title}\n{ticker}'


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

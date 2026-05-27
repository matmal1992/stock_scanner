import json
import os
import urllib.parse
import urllib.request
from typing import Final

TELEGRAM_BOT_TOKEN_ENV: Final[str] = "TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID_ENV: Final[str] = "TELEGRAM_CHAT_ID"


def get_telegram_config() -> tuple[str | None, str | None]:
    return os.getenv(TELEGRAM_BOT_TOKEN_ENV), os.getenv(TELEGRAM_CHAT_ID_ENV)


def send_telegram_message(message: str) -> bool:
    bot_token, chat_id = get_telegram_config()
    if not bot_token or not chat_id:
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
    }
    data = urllib.parse.urlencode(payload).encode("utf-8")

    request = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8")
        result = json.loads(body)
        return bool(result.get("ok", False))
    except Exception:
        return False

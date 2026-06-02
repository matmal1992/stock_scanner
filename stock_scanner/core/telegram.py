import json
import traceback
import urllib.parse
import urllib.request

from stock_scanner.download.config import load_config

config = load_config()
telegram_token = config.get("telegram_bot_token")
telegram_chat_id = config.get("telegram_chat_id")


def send_telegram_message(message: str) -> bool:
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    payload = {
        "chat_id": telegram_chat_id,
        "text": message,
        # "parse_mode": "HTML",
    }
    data = urllib.parse.urlencode(payload).encode("utf-8")

    request = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8")
            print("TELEGRAM RESPONSE:", body)
        result = json.loads(body)
        return bool(result.get("ok", False))
    except Exception as e:
        print("TELEGRAM ERROR TYPE:", type(e))
        print("TELEGRAM ERROR:", e)
        print(traceback.format_exc())
        return False

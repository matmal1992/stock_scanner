import json
import logging
import urllib.parse
import urllib.request

from src.stock_scanner.core.database import Database
from src.stock_scanner.core.paths import configure_environment, get_assets_dir
from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository
from src.stock_scanner.workers.telegram import TelegramBot

logger = logging.getLogger(__name__)

PAP_URL = "https://espiebi.pap.pl/node/739060"


def send_text_message(token: str, chat_id: int | str, text: str) -> int | None:
    """Wysyła wiadomość tekstową i zwraca jej message_id."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    data = urllib.parse.urlencode(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST")

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
            if result.get("ok"):
                return result["result"]["message_id"]
    except Exception as e:
        print(f"Błąd wysyłania tekstu: {e}")
    return None


def send_photo_bytes(token: str, chat_id: int | str) -> int | None:
    """Wysyła zdjęcie z surowych bajtów (bytes) i zwraca jego message_id."""
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    boundary = "----TelegramBoundaryBytes"

    image_path = get_assets_dir() / "input_icon.png"

    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
    except Exception as e:
        print(f"Błąd odczytu pliku z dysku: {e}")
        return None

    body = (
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="chat_id"\r\n\r\n'
            f"{chat_id}\r\n"
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="photo"; filename="some_name"\r\n'
            f"Content-Type: image/png\r\n\r\n"
        ).encode("utf-8")
        + image_bytes
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
                return result["result"]["message_id"]
    except Exception as e:
        print(f"Błąd wysyłania zdjęcia: {e}")
    return None


def send_both_messages(token: str, chat_id: int | str) -> None:
    text_id = send_text_message(token, chat_id, "text message")
    print(f"Wysłano wiadomość tekstową, ID: {text_id}")

    photo_id = send_photo_bytes(token, chat_id)
    print(f"Wysłano zdjęcie z bajtów, ID: {photo_id}")

    print(text_id)
    print(photo_id)


def get_latest_message_info(token: str) -> None:
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            for update in data.get("result", []):
                # Sprawdzamy wiadomości zwykłe lub edytowane
                msg = update.get("message") or update.get("edited_message")
                if msg:
                    chat = msg["chat"]
                    print(f"Chat ID: {chat['id']} (typ: {chat['type']})")
                    print(f"Message ID: {msg['message_id']}")
                    print(f"Treść: {msg.get('text')}")
                    print("-" * 30)
    except Exception as e:
        print("Błąd pobierania update'ów:", e)


def send_initial_log_file(token: str, chat_id: int | str, log_content: str) -> int | None:
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    boundary = "----TelegramBoundaryLog"

    file_bytes = log_content.encode("utf-8")

    body = (
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="chat_id"\r\n\r\n'
            f"{chat_id}\r\n"
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="caption"\r\n\r\n'
            f"\r\n"
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="document"; filename="error_log.txt"\r\n'
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
            print(result["result"]["message_id"])
            return result["result"]["message_id"]
        else:
            print(f"Telegram API error: {result}")
    except Exception as e:
        print(f"Błąd wysyłania pliku logu: {e}")

    return None


def test_telegram() -> None:
    db = Database()
    db.init_db()

    entry_repo = EntryRepository(db)
    TelegramBot.init(entry_repo)
    TelegramBot.send_message("Telegram alert")


def main() -> None:
    pass


if __name__ == "__main__":
    configure_environment()
    main()

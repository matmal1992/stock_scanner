import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from stock_scanner.download.config import email_config_path


def _load_config() -> dict | None:
    if not email_config_path.exists():
        print(f"CONFIG NOT FOUND: {email_config_path}")
        return None

    try:
        with open(email_config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"CONFIG ERROR: {e}")
        return None


def send_gmail_alert(subject: str, message: str) -> bool:
    config = _load_config()
    if not config:
        return False

    gmail_address = config.get("gmail_address")
    gmail_password = config.get("gmail_password")
    recipient = config.get("recipient")

    if not gmail_address or not gmail_password or not recipient:
        print("CONFIG INCOMPLETE")
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = gmail_address
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "html"))

        with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
            server.starttls()
            server.login(gmail_address, gmail_password)
            server.send_message(msg)

        print("EMAIL SENT")
        return True

    except Exception as e:
        print(f"EMAIL ERROR: {e}")
        return False

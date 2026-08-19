import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.stock_scanner.download.config import load_config

logger = logging.getLogger(__name__)


def send_gmail_alert(subject: str, message: str) -> bool:
    config = load_config()
    gmail_address = config.get("gmail_address")
    gmail_password = config.get("gmail_password")
    recipient = config.get("recipient")

    if not gmail_address or not gmail_password or not recipient:
        logger.warning("CONFIG INCOMPLETE")
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

        logger.info("EMAIL SENT")
        return True

    except Exception as e:
        logger.error(f"EMAIL ERROR: {e}")
        return False

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from stock_scanner.download.config import load_config


def send_gmail_alert(subject: str, message: str) -> bool:
    config = load_config()
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

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

GMAIL_ADDRESS_ENV = "GMAIL_ADDRESS"
GMAIL_PASSWORD_ENV = "GMAIL_PASSWORD"
GMAIL_RECIPIENT_ENV = "GMAIL_RECIPIENT"

#  dodac config.json i wczytywac z niego dane do logowania


def get_gmail_config() -> tuple[str | None, str | None, str | None]:
    """Get Gmail configuration from environment variables."""
    return (
        os.getenv(GMAIL_ADDRESS_ENV),
        os.getenv(GMAIL_PASSWORD_ENV),
        os.getenv(GMAIL_RECIPIENT_ENV),
    )


def send_gmail_alert(subject: str, message: str) -> bool:
    """Send email alert via Gmail SMTP.

    Args:
        subject: Email subject
        message: Email body (can contain HTML)

    Returns:
        True if email was sent successfully, False otherwise
    """
    gmail_address, gmail_password, recipient = get_gmail_config()

    if not gmail_address or not gmail_password or not recipient:
        return False

    try:
        # Create email message
        msg = MIMEMultipart()
        msg["From"] = gmail_address
        msg["To"] = recipient
        msg["Subject"] = subject

        # Attach HTML body
        msg.attach(MIMEText(message, "html"))

        # Send email via Gmail SMTP
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
            server.starttls()
            server.login(gmail_address, gmail_password)
            server.send_message(msg)

        return True
    except Exception:
        return False

import os
import smtplib
from email.message import EmailMessage

from content import BUSINESS

DEFAULT_TO = BUSINESS["email_service"]


def _smtp_settings():
    return {
        "host": os.environ.get("SMTP_HOST", "smtp.gmail.com"),
        "port": int(os.environ.get("SMTP_PORT", "587")),
        "user": os.environ.get("SMTP_USER", "").strip(),
        "password": os.environ.get("SMTP_PASSWORD", "").strip(),
        "from_addr": os.environ.get("MAIL_FROM", os.environ.get("SMTP_USER", DEFAULT_TO)).strip(),
        "to": os.environ.get("MAIL_TO", DEFAULT_TO).strip() or DEFAULT_TO,
    }


def send_mail(subject, body, *, reply_to=None, to=None, suppress=False):
    """Send plain-text mail. Returns True on success (or when suppressed)."""
    if suppress:
        return True
    cfg = _smtp_settings()
    if not cfg["user"] or not cfg["password"]:
        return False
    recipient = (to or cfg["to"] or DEFAULT_TO).strip()
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = cfg["from_addr"] or cfg["user"]
    msg["To"] = recipient
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content(body)
    with smtplib.SMTP(cfg["host"], cfg["port"], timeout=30) as smtp:
        smtp.starttls()
        smtp.login(cfg["user"], cfg["password"])
        smtp.send_message(msg)
    return True

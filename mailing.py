import json
import logging
import os
import smtplib
import urllib.error
import urllib.request
from email.message import EmailMessage

from content import BUSINESS

log = logging.getLogger(__name__)

DEFAULT_TO = BUSINESS["email_service"]


def format_order_mail(placed):
    """Build subject and plain-text body for a placed order."""
    lines = [f"Vittorio order {placed['ref']}"]
    if placed.get("business_name"):
        lines.append(placed["business_name"])
    lines.append(f"{placed['town']}, Cyprus")
    lines.append(f"Contact: {placed['name']} <{placed['email']}>, {placed.get('phone', '')}")
    if placed.get("notes"):
        lines.append(f"Notes: {placed['notes']}")
    for line in placed.get("lines") or []:
        lines.append(f"{line['qty']} × {line['name']} ({line['line_total']})")
    if placed.get("subtotal"):
        lines.append(f"Priced lines {placed['subtotal']} + VAT")
    lines.append("Payment: cash on delivery only.")
    subject = f"Vittorio order {placed['ref']}"
    return subject, "\n".join(lines)


def _smtp_settings():
    return {
        "host": os.environ.get("SMTP_HOST", "smtp.gmail.com"),
        "port": int(os.environ.get("SMTP_PORT", "587")),
        "user": os.environ.get("SMTP_USER", "").strip(),
        "password": os.environ.get("SMTP_PASSWORD", "").strip(),
        "from_addr": os.environ.get("MAIL_FROM", os.environ.get("SMTP_USER", DEFAULT_TO)).strip(),
        "to": os.environ.get("MAIL_TO", DEFAULT_TO).strip() or DEFAULT_TO,
    }


def _send_smtp(subject, body, *, reply_to=None, to=None):
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


def _send_web3forms(subject, body, *, reply_to=None):
    key = os.environ.get("WEB3FORMS_ACCESS_KEY", "").strip()
    if not key:
        return False
    payload = {
        "access_key": key,
        "subject": subject,
        "from_name": "Vittorio website",
        "email": reply_to or DEFAULT_TO,
        "message": body,
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        "https://api.web3forms.com/submit",
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))
    if not result.get("success"):
        log.warning("Web3Forms rejected mail: %s", result)
        return False
    return True


def _send_formsubmit(subject, body, *, reply_to=None):
    """Backup relay; first use requires confirming FormSubmit in the inbox once."""
    payload = {
        "_subject": subject,
        "_replyto": reply_to or "",
        "message": body,
        "_captcha": "false",
        "_template": "table",
    }
    data = json.dumps(payload).encode("utf-8")
    url = f"https://formsubmit.co/ajax/{DEFAULT_TO}"
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))
    return bool(result.get("success"))


def send_mail(subject, body, *, reply_to=None, to=None, suppress=False):
    """Send plain-text mail to the depot. Tries SMTP, then Web3Forms, then FormSubmit."""
    if suppress:
        return True
    attempts = (
        ("smtp", lambda: _send_smtp(subject, body, reply_to=reply_to, to=to)),
        ("web3forms", lambda: _send_web3forms(subject, body, reply_to=reply_to)),
        ("formsubmit", lambda: _send_formsubmit(subject, body, reply_to=reply_to)),
    )
    for name, sender in attempts:
        try:
            if sender():
                log.info("Depot mail sent via %s", name)
                return True
        except (OSError, urllib.error.URLError, smtplib.SMTPException, ValueError) as err:
            log.warning("Depot mail via %s failed: %s", name, err)
    log.error(
        "Depot mail not sent; configure SMTP_PASSWORD on Render and/or WEB3FORMS_ACCESS_KEY"
    )
    return False

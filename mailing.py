import json
import logging
import os
import smtplib
import urllib.error
import urllib.request
from email.message import EmailMessage
from pathlib import Path

from urllib.parse import quote

from content import BUSINESS
from i18n import localize_pack, translate

log = logging.getLogger(__name__)

DEFAULT_TO = BUSINESS["email_service"]
# FormSubmit only delivers requests that name the site they came from, and its
# one-time activation is tied to that page, so keep this URL stable.
SITE_URL = os.environ.get("SITE_URL", "https://vittorio-coffee.onrender.com").rstrip("/")
FORMSUBMIT_REFERER = f"{SITE_URL}/order"
# Keep every attempt short so a blocked port cannot outlast gunicorn's 30s worker timeout.
SMTP_TIMEOUT = 8
HTTP_TIMEOUT = 12

_SECRET_FILE_NAMES = (
    "smtp_password",
    "SMTP_PASSWORD",
    "gmail_app_password",
)


def viber_order_href(order_body):
    """Deep link to the depot Viber chat with the order text prefilled."""
    base = BUSINESS["viber"].rstrip("/")
    encoded = quote(order_body, safe="")
    return f"{base}&text={encoded}&draft={encoded}"


def format_order_mail(placed):
    """Build subject and plain-text body for a placed order."""
    lines = [
        f"Vittorio order {placed['ref']}",
        "",
        "Customer details",
        f"Name: {placed.get('name', '')}",
        f"Email: {placed.get('email', '')}",
        f"Phone: {placed.get('phone', '')}",
        f"Town: {placed.get('town', '')}, Cyprus",
    ]
    if placed.get("business_name"):
        lines.append(f"Café or bar: {placed['business_name']}")
    if placed.get("notes"):
        lines.append(f"Notes: {placed['notes']}")
    if placed.get("lang") == "el":
        lines.append("Language: Greek (ordered on the Greek site)")
    lines.extend(["", "Order", "Qty\tPack\tProduct\tLine"])
    for line in placed.get("lines") or []:
        pack = (line.get("pack") or "").strip() or "—"
        lines.append(f"{line['qty']}\t{pack}\t{line['name']}\t{line['line_total']}")
    lines.extend(_totals_block(placed))
    subject = f"Vittorio order {placed['ref']}"
    return subject, "\n".join(lines)


def _totals_block(placed, lang="en"):
    def t(text):
        return translate(text, lang)

    totals = placed.get("totals")
    lines = []
    if totals:
        lines.extend(
            [
                "",
                f"{t('Subtotal (ex VAT)')}: {totals['subtotal']}",
                f"{t('VAT')} ({totals['vat_label']}): {totals['vat']}",
                f"{t('Delivery')}: {t(totals['delivery'])}",
                f"{t('Total to pay on delivery')}: {totals['total']}",
            ]
        )
    elif placed.get("subtotal"):
        lines.append(f"{t('Subtotal (ex VAT)')}: {placed['subtotal']}")
    lines.append(t("Payment: cash on delivery only."))
    return lines


def format_customer_copy(placed, reorder_url, lang="en"):
    """Receipt emailed to the customer in the site's language, with a link that refills the same order."""

    def t(text, **values):
        return translate(text, lang, **values)

    lines = [
        t("Dear {name},", name=placed.get("name", "")),
        "",
        t("Thank you for your order with {business}. We will confirm it before delivery.", business=BUSINESS["name"]),
        "",
        t("Order reference: {ref}", ref=placed["ref"]),
        t("Delivery to: {town}, Cyprus", town=placed.get("town", "")),
    ]
    if placed.get("business_name"):
        lines.append(t("Business: {name}", name=placed["business_name"]))
    lines.append("")
    for line in placed.get("lines") or []:
        pack = localize_pack((line.get("pack") or "").strip(), lang)
        pack_text = f" ({pack})" if pack else ""
        lines.append(f"{line['qty']} x {line['name']}{pack_text}: {t(line['line_total'])}")
    lines.extend(_totals_block(placed, lang))
    lines.extend(
        [
            "",
            t("Order the same again:"),
            reorder_url,
            "",
            t("Questions about your order? Reply to this email."),
            "",
            BUSINESS["name"],
            ", ".join(t(part) for part in (BUSINESS["locality"], BUSINESS["region"], BUSINESS["country"])),
        ]
    )
    return t("Your Vittorio order {ref}", ref=placed["ref"]), "\n".join(lines)


def _normalize_app_password(raw):
    """Gmail app passwords are 16 chars; Google often displays them in four groups."""
    return (raw or "").strip().replace(" ", "")


def _read_smtp_password():
    for key in ("SMTP_PASSWORD", "GMAIL_APP_PASSWORD"):
        value = _normalize_app_password(os.environ.get(key, ""))
        if value:
            return value
    file_hint = os.environ.get("SMTP_PASSWORD_FILE", "").strip()
    candidates = []
    if file_hint:
        candidates.append(file_hint)
    candidates.extend(f"/etc/secrets/{name}" for name in _SECRET_FILE_NAMES)
    for path in candidates:
        try:
            if path and os.path.isfile(path):
                return _normalize_app_password(Path(path).read_text(encoding="utf-8"))
        except OSError as err:
            log.warning("Could not read SMTP secret file %s: %s", path, err)
    return ""


def mail_transport_status():
    """Non-secret snapshot for /health/mail (debug Render env injection)."""
    password = _read_smtp_password()
    web3 = bool(os.environ.get("WEB3FORMS_ACCESS_KEY", "").strip())
    cfg = _smtp_settings()
    return {
        "smtp_user_env_set": bool(os.environ.get("SMTP_USER", "").strip()),
        "smtp_user_effective": cfg["user"],
        "smtp_password_chars": len(password),
        "web3forms_configured": web3,
        "mail_to": cfg["to"],
    }


def _smtp_settings():
    user = os.environ.get("SMTP_USER", "").strip() or DEFAULT_TO
    return {
        "host": os.environ.get("SMTP_HOST", "smtp.gmail.com").strip() or "smtp.gmail.com",
        "port": int(os.environ.get("SMTP_PORT", "587")),
        "user": user,
        "password": _read_smtp_password(),
        "from_addr": (os.environ.get("MAIL_FROM", "").strip() or user or DEFAULT_TO),
        "to": os.environ.get("MAIL_TO", DEFAULT_TO).strip() or DEFAULT_TO,
    }


def _send_smtp_starttls(cfg, msg):
    with smtplib.SMTP(cfg["host"], cfg["port"], timeout=SMTP_TIMEOUT) as smtp:
        smtp.starttls()
        smtp.login(cfg["user"], cfg["password"])
        smtp.send_message(msg)


def _send_smtp_ssl(cfg, msg):
    with smtplib.SMTP_SSL(cfg["host"], 465, timeout=SMTP_TIMEOUT) as smtp:
        smtp.login(cfg["user"], cfg["password"])
        smtp.send_message(msg)


def _send_smtp(subject, body, *, reply_to=None, to=None):
    cfg = _smtp_settings()
    if not cfg["password"]:
        log.warning(
            "SMTP password missing (set SMTP_PASSWORD on the web service, or upload "
            "Render Secret File named smtp_password under /etc/secrets/)"
        )
        return False
    recipient = (to or cfg["to"] or DEFAULT_TO).strip()
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = cfg["from_addr"] or cfg["user"]
    msg["To"] = recipient
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content(body)
    try:
        _send_smtp_starttls(cfg, msg)
        return True
    except smtplib.SMTPException as first_err:
        log.warning("Depot mail via smtp (port %s) failed: %s", cfg["port"], first_err)
    try:
        _send_smtp_ssl(cfg, msg)
        return True
    except smtplib.SMTPException as second_err:
        log.warning("Depot mail via smtp (ssl 465) failed: %s", second_err)
        raise second_err


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
        "botcheck": False,
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        "https://api.web3forms.com/submit",
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
        result = json.loads(response.read().decode("utf-8"))
    if not result.get("success"):
        log.warning("Web3Forms rejected mail: %s", result)
        return False
    return True


def _send_formsubmit(subject, body, *, reply_to=None):
    """Relay that works on Render's free plan, which blocks outbound SMTP ports.

    First use needs the 'Activate Form' link that FormSubmit emails to the inbox.
    """
    payload = {
        "_subject": subject,
        "_replyto": reply_to or "",
        "message": body,
        "_captcha": "false",
        "_template": "table",
    }
    data = json.dumps(payload).encode("utf-8")
    url = f"https://formsubmit.co/ajax/{quote(DEFAULT_TO)}"
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Vittorio-Coffee/1.0",
            "Origin": SITE_URL,
            "Referer": FORMSUBMIT_REFERER,
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
        result = json.loads(response.read().decode("utf-8"))
    # FormSubmit answers {"success": "false"} as a string, which is truthy.
    if str(result.get("success")).lower() != "true":
        log.warning("FormSubmit rejected mail: %s", result)
        return False
    return True


def send_customer_copy(subject, body, to, *, suppress=False):
    """Email the customer from the depot Gmail. Only SMTP can reach arbitrary addresses."""
    if suppress:
        return True
    if not _read_smtp_password():
        return False
    try:
        if _send_smtp(subject, body, reply_to=DEFAULT_TO, to=to):
            log.info("Customer copy sent for %s", subject)
            return True
    except (OSError, smtplib.SMTPException, ValueError) as err:
        log.warning("Customer copy failed for %s: %s", subject, err)
    return False


def send_mail(subject, body, *, reply_to=None, to=None, suppress=False):
    """Send plain-text mail to the depot. Tries SMTP, then Web3Forms, then FormSubmit."""
    if suppress:
        return True
    status = mail_transport_status()
    attempts = []
    if status["smtp_password_chars"]:
        attempts.append(("smtp", lambda: _send_smtp(subject, body, reply_to=reply_to, to=to)))
    if status["web3forms_configured"]:
        attempts.append(("web3forms", lambda: _send_web3forms(subject, body, reply_to=reply_to)))
    if not attempts:
        attempts.append(("smtp", lambda: _send_smtp(subject, body, reply_to=reply_to, to=to)))
        attempts.append(("web3forms", lambda: _send_web3forms(subject, body, reply_to=reply_to)))
    attempts.append(("formsubmit", lambda: _send_formsubmit(subject, body, reply_to=reply_to)))

    for name, sender in attempts:
        try:
            if sender():
                log.info("Depot mail sent via %s", name)
                return True
        except (OSError, urllib.error.URLError, smtplib.SMTPException, ValueError) as err:
            log.warning("Depot mail via %s failed: %s", name, err)
    log.error(
        "Depot mail not sent; smtp_password_chars=%s web3forms=%s",
        status["smtp_password_chars"],
        status["web3forms_configured"],
    )
    return False

import os

import mailing


def test_normalize_app_password_strips_spaces():
    assert mailing._normalize_app_password("abcd efgh ijkl mnop") == "abcdefghijklmnop"


def test_read_smtp_password_from_env(monkeypatch):
    monkeypatch.setenv("SMTP_PASSWORD", "abcd efgh ijkl mnop")
    assert mailing._read_smtp_password() == "abcdefghijklmnop"


def test_mail_transport_status(monkeypatch):
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)
    monkeypatch.delenv("GMAIL_APP_PASSWORD", raising=False)
    monkeypatch.delenv("SMTP_USER", raising=False)
    status = mailing.mail_transport_status()
    assert status["smtp_user_env_set"] is False
    assert status["smtp_user_effective"] == mailing.DEFAULT_TO
    assert status["smtp_password_chars"] == 0


def test_smtp_settings_default_user_to_depot_email(monkeypatch):
    monkeypatch.delenv("SMTP_USER", raising=False)
    monkeypatch.delenv("MAIL_FROM", raising=False)
    cfg = mailing._smtp_settings()
    assert cfg["user"] == mailing.DEFAULT_TO
    assert cfg["from_addr"] == mailing.DEFAULT_TO


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._payload.encode("utf-8")


def test_formsubmit_string_false_is_a_failure(monkeypatch):
    sent = {}

    def fake_urlopen(request, timeout):
        sent["headers"] = dict(request.header_items())
        return _FakeResponse('{"success":"false","message":"This form needs Activation."}')

    monkeypatch.setattr(mailing.urllib.request, "urlopen", fake_urlopen)
    assert mailing._send_formsubmit("Vittorio order X", "body") is False
    assert sent["headers"]["Referer"] == mailing.FORMSUBMIT_REFERER
    assert sent["headers"]["Origin"] == mailing.FORMSUBMIT_ORIGIN


def test_formsubmit_string_true_is_a_success(monkeypatch):
    monkeypatch.setattr(
        mailing.urllib.request,
        "urlopen",
        lambda request, timeout: _FakeResponse('{"success":"true","message":"The form was submitted successfully."}'),
    )
    assert mailing._send_formsubmit("Vittorio order X", "body") is True


def test_customer_copy_lists_items_totals_and_reorder_link():
    placed = {
        "ref": "ABC123",
        "name": "Koxar",
        "address": "Makariou 12, 1st floor", "town": "Larnaca",
        "business_name": "Harbour Bar",
        "lines": [{"slug": "costa-rica", "name": "Costa Rica", "qty": 2, "pack": "0.5 kg", "line_total": "€29.20"}],
        "totals": {"subtotal": "€29.20", "vat_label": "5%", "vat": "€1.46", "delivery": "€5.00", "total": "€35.66"},
    }
    subject, body = mailing.format_customer_copy(placed, "https://example.test/order/again?items=costa-rica:2")
    assert subject == "Your Vittorio order ABC123"
    assert "2 x Costa Rica (0.5 kg): €29.20" in body
    assert "Total to pay on delivery: €35.66" in body
    assert "https://example.test/order/again?items=costa-rica:2" in body


def test_customer_copy_goes_to_customer_via_smtp(monkeypatch):
    calls = {}
    monkeypatch.setenv("SMTP_PASSWORD", "abcdefghijklmnop")

    def fake_send_smtp(subject, body, *, reply_to=None, to=None):
        calls.update(subject=subject, reply_to=reply_to, to=to)
        return True

    monkeypatch.setattr(mailing, "_send_smtp", fake_send_smtp)
    assert mailing.send_customer_copy("Your Vittorio order X", "body", "cafe@example.com") is True
    assert calls["to"] == "cafe@example.com"
    assert calls["reply_to"] == mailing.DEFAULT_TO


def test_customer_copy_skipped_without_smtp(monkeypatch):
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)
    monkeypatch.delenv("GMAIL_APP_PASSWORD", raising=False)
    monkeypatch.setattr(mailing, "_read_smtp_password", lambda: "")
    assert mailing.send_customer_copy("Your Vittorio order X", "body", "cafe@example.com") is False

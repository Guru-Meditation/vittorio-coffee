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
    assert sent["headers"]["Origin"] == mailing.SITE_URL


def test_formsubmit_string_true_is_a_success(monkeypatch):
    monkeypatch.setattr(
        mailing.urllib.request,
        "urlopen",
        lambda request, timeout: _FakeResponse('{"success":"true","message":"The form was submitted successfully."}'),
    )
    assert mailing._send_formsubmit("Vittorio order X", "body") is True

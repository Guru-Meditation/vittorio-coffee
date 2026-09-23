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
    monkeypatch.setenv("SMTP_USER", "user@example.com")
    status = mailing.mail_transport_status()
    assert status["smtp_user_set"] is True
    assert status["smtp_password_chars"] == 0

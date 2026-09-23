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

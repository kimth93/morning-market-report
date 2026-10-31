from __future__ import annotations

import datetime as dt
import json

import pytest

from app.cli import approve_and_send as cli

CSV_TEXT = (
    "name,email,consent,created_at\n"
    "김투자,approved@example.com,on,2026-10-30\n"
    "이승인,not-approved@example.com,on,2026-10-30\n"
    "박동의,consent-missing@example.com,,2026-10-30\n"
    "최중복,approved@example.com,on,2026-10-31\n"
)
APPROVED_TEXT = "# 승인한 주소만 적는다\napproved@example.com\nconsent-missing@example.com\n"


@pytest.fixture
def files(tmp_path):
    csv_path = tmp_path / "submissions.csv"
    csv_path.write_text(CSV_TEXT, encoding="utf-8")
    approved_path = tmp_path / "approved.txt"
    approved_path.write_text(APPROVED_TEXT, encoding="utf-8")
    return csv_path, approved_path, tmp_path / "sent-log.json"


class SpySender:
    def __init__(self):
        self.sent: list[str] = []

    def send(self, to: str, subject: str, body: str) -> str:
        self.sent.append(to)
        return f"msg-{len(self.sent)}"


def test_recipients_need_both_approval_and_consent_and_are_unique(files):
    csv_path, approved_path, _ = files

    recipients = cli.select_recipients(csv_path, approved_path)

    assert recipients == ["approved@example.com"]


def test_dry_run_is_the_default_and_sends_nothing(files):
    csv_path, approved_path, log_path = files
    sender = SpySender()

    plan = cli.run(csv_path, approved_path, log_path, sender=sender, send=False, today=dt.date(2026, 10, 31))

    assert plan.recipients == ["approved@example.com"]
    assert plan.dry_run is True
    assert sender.sent == []
    assert not log_path.exists()


def test_send_without_a_real_sender_is_refused(files):
    csv_path, approved_path, log_path = files

    with pytest.raises(cli.SenderNotConfigured):
        cli.run(csv_path, approved_path, log_path, sender=None, send=True, today=dt.date(2026, 10, 31))


def test_send_calls_sender_once_per_recipient_and_logs_it(files):
    csv_path, approved_path, log_path = files
    sender = SpySender()

    cli.run(csv_path, approved_path, log_path, sender=sender, send=True, today=dt.date(2026, 10, 31))

    assert sender.sent == ["approved@example.com"]
    log = json.loads(log_path.read_text(encoding="utf-8"))
    assert log["2026-10-31"] == ["approved@example.com"]


def test_same_day_run_does_not_send_twice(files):
    csv_path, approved_path, log_path = files
    sender = SpySender()
    day = dt.date(2026, 10, 31)

    cli.run(csv_path, approved_path, log_path, sender=sender, send=True, today=day)
    second = cli.run(csv_path, approved_path, log_path, sender=sender, send=True, today=day)

    assert sender.sent == ["approved@example.com"]
    assert second.recipients == []

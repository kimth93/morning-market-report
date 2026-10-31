"""로컬에서만 실행한다. Netlify Forms 신청 CSV와 승인 목록을 맞춰 발송 대상을 정한다.

기본은 dry-run(계획만 출력)이다. --send를 주고 실발송 구현체가 연결되어 있어야만 실제로 보낸다.

실행 예:
  python3 -m app.cli.approve_and_send --csv submissions.csv --approved approved.txt
  python3 -m app.cli.approve_and_send --csv submissions.csv --approved approved.txt --send
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Protocol, Sequence

CONSENT_VALUES = {"on", "true", "1", "yes", "y"}
DEFAULT_LOG = Path(__file__).resolve().parent.parent.parent / "outbox" / "sent-log.json"


class SenderNotConfigured(Exception):
    """실발송 구현체가 아직 없을 때 --send를 막는다."""


class Sender(Protocol):
    def send(self, to: str, subject: str, body: str) -> str: ...


@dataclass
class Plan:
    recipients: list[str]
    dry_run: bool
    sent: list[str] = field(default_factory=list)


def _normalize(email: str) -> str:
    return email.strip().lower()


def load_approved(path: Path) -> set[str]:
    approved = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            approved.add(_normalize(line))
    return approved


def select_recipients(csv_path: Path, approved_path: Path) -> list[str]:
    approved = load_approved(approved_path)
    recipients: list[str] = []
    with csv_path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            email = _normalize(row.get("email", ""))
            consented = (row.get("consent") or "").strip().lower() in CONSENT_VALUES
            if email and consented and email in approved and email not in recipients:
                recipients.append(email)
    return recipients


def _load_log(path: Path) -> dict[str, list[str]]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def run(
    csv_path: Path,
    approved_path: Path,
    log_path: Path,
    sender: Optional[Sender],
    send: bool,
    today: dt.date,
    subject: str = "[아침 시장 전망] 오늘의 시장 브리핑",
    body: str = "",
) -> Plan:
    if send and sender is None:
        raise SenderNotConfigured("실발송 구현체가 아직 연결되지 않았습니다. 시연 시점에 추가합니다.")

    day_key = today.isoformat()
    log = _load_log(log_path)
    already_sent = set(log.get(day_key, []))
    recipients = [r for r in select_recipients(csv_path, approved_path) if r not in already_sent]

    if not send:
        return Plan(recipients=recipients, dry_run=True)

    sent: list[str] = []
    for to in recipients:
        sender.send(to, subject, body)
        sent.append(to)
    if sent:
        log.setdefault(day_key, []).extend(sent)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return Plan(recipients=recipients, dry_run=False, sent=sent)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="승인된 신청자에게만 발송 대상을 정합니다.")
    parser.add_argument("--csv", type=Path, required=True, help="Netlify Forms에서 내려받은 신청 CSV")
    parser.add_argument("--approved", type=Path, required=True, help="승인한 이메일 목록(한 줄에 하나)")
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG, help="발송 기록 파일")
    parser.add_argument("--send", action="store_true", help="실제로 발송합니다 (기본은 dry-run)")
    args = parser.parse_args(argv)

    try:
        plan = run(args.csv, args.approved, args.log, sender=None, send=args.send, today=dt.date.today())
    except SenderNotConfigured as exc:
        print(f"중단: {exc}")
        return 2

    if plan.dry_run:
        print(f"[dry-run] 발송 대상 {len(plan.recipients)}명 (실제 발송 없음)")
        for email in plan.recipients:
            print(f"  - {email}")
    else:
        print(f"발송 {len(plan.sent)}명")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

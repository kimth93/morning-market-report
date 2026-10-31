"""로컬에서만 실행한다. 보고서를 한 번 생성해 정적 사이트용 report.json으로 저장한다.

실행: cd backend && python3 -m app.cli.export_snapshot --out ../frontend/public/report.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Optional, Sequence

from app.config import get_settings
from app.db import init_db, make_engine, make_session_factory
from app.services.report import generate_report

SOURCE_NOTE = "개발자가 생성한 예시 보고서입니다. 실시간 생성 결과가 아닙니다."
DEFAULT_OUT = Path(__file__).resolve().parent.parent.parent.parent / "frontend" / "public" / "report.json"


def write_snapshot(report: dict[str, Any], out: Path) -> None:
    payload = {
        "news_items": report["news_items"],
        "market_outlook": report["market_outlook"],
        "investment_points": report["investment_points"],
        "generated_at": report["generated_at"],
        "source_note": SOURCE_NOTE,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_session():
    settings = get_settings()
    engine = make_engine(settings.database_url)
    init_db(engine)
    return make_session_factory(engine)()


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="보고서를 한 번 생성해 report.json으로 저장합니다.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    settings = get_settings()
    session = load_session()
    try:
        report = generate_report(session, settings)
    finally:
        session.close()
    write_snapshot(report, args.out)
    print(f"저장했습니다: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

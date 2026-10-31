from __future__ import annotations

import json

from app.cli import export_snapshot as cli

REPORT = {
    "news_items": [{"title": "기사", "source": "한국경제", "date": "2026-10-31", "url": "https://www.hankyung.com/a", "summary": "요약.", "hallucination_risk": "low"}],
    "market_outlook": "전망 한 문단.",
    "investment_points": ["a", "b", "c"],
    "generated_at": "2026-10-31T07:00:00+00:00",
}


def test_write_snapshot_writes_public_json_with_source_note(tmp_path):
    out = tmp_path / "public" / "report.json"

    cli.write_snapshot(REPORT, out)

    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["news_items"] == REPORT["news_items"]
    assert data["market_outlook"] == "전망 한 문단."
    assert data["investment_points"] == ["a", "b", "c"]
    assert data["generated_at"] == REPORT["generated_at"]
    assert "예시" in data["source_note"]


def test_main_generates_once_and_writes_snapshot(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(cli, "load_session", lambda: type("S", (), {"close": lambda self: None})())
    monkeypatch.setattr(cli, "get_settings", lambda: object())
    monkeypatch.setattr(cli, "generate_report", lambda session, settings: calls.append(1) or REPORT)
    out = tmp_path / "report.json"

    exit_code = cli.main(["--out", str(out)])

    assert exit_code == 0
    assert len(calls) == 1
    assert json.loads(out.read_text(encoding="utf-8"))["market_outlook"] == "전망 한 문단."

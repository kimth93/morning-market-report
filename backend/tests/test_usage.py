from __future__ import annotations

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.db import init_db, make_engine, make_session_factory
from app.main import app
from app.models import ApiUsage
from app.services.usage import PRICES_PER_MTOK, aggregate_usage, record_usage


@pytest.fixture
def session(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'usage.db'}")
    init_db(engine)
    session = make_session_factory(engine)()
    yield session
    session.close()


def add(session, day: int, input_tokens: int, output_tokens: int, model="claude-opus-5-5", kind="summary"):
    record_usage(
        session,
        kind=kind,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        now=datetime(2026, 10, day, 9, 0),
    )
    session.commit()


def test_daily_aggregate_sums_calls_and_tokens_per_day(session):
    add(session, 30, 100, 10)
    add(session, 30, 200, 20)
    add(session, 31, 50, 5)

    rows = aggregate_usage(session, "daily")

    assert [(r["period"], r["calls"], r["input_tokens"], r["output_tokens"]) for r in rows] == [
        ("2026-10-30", 2, 300, 30),
        ("2026-10-31", 1, 50, 5),
    ]


def test_monthly_aggregate_merges_days_in_same_month(session):
    add(session, 30, 100, 10)
    add(session, 31, 200, 20)

    rows = aggregate_usage(session, "monthly")

    assert len(rows) == 1
    assert rows[0]["period"] == "2026-10"
    assert rows[0]["calls"] == 2


def test_estimated_cost_uses_per_million_token_prices(session):
    input_price, output_price = PRICES_PER_MTOK["claude-opus-5-5"]
    add(session, 30, 1_000_000, 500_000)

    row = aggregate_usage(session, "daily")[0]

    assert row["estimated_cost_usd"] == pytest.approx(input_price * 1 + output_price * 0.5)


def test_unknown_model_has_no_cost_estimate(session):
    add(session, 30, 100, 10, model="unknown-model")

    row = aggregate_usage(session, "daily")[0]

    assert row["estimated_cost_usd"] is None


def test_usage_endpoint_returns_rows_and_rejects_unknown_period(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAUDE_API_KEY", "test-claude-key")
    monkeypatch.setenv("NAVER_CLIENT_ID", "test-naver-id")
    monkeypatch.setenv("NAVER_CLIENT_SECRET", "test-naver-secret")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'endpoint.db'}")

    with TestClient(app) as client:
        session = app.state.session_factory()
        add(session, 30, 100, 10)
        session.close()

        ok = client.get("/api/usage", params={"period": "daily"})
        bad = client.get("/api/usage", params={"period": "hourly"})

    assert ok.status_code == 200
    body = ok.json()
    assert body["period"] == "daily"
    assert body["rows"][0]["calls"] == 1
    assert "pricing_note" in body
    assert bad.status_code == 422


def test_summarize_and_store_records_one_usage_row_per_new_summary(tmp_path):
    from app.models import NewsItem
    from app.services.summarizer import summarize_and_store
    from tests.test_summarizer import FakeClient, GOOD_SUMMARY, news, reply

    engine = make_engine(f"sqlite:///{tmp_path / 'summ.db'}")
    init_db(engine)
    session = make_session_factory(engine)()
    items = [news("기사 1", "https://www.hankyung.com/1"), news("기사 2", "https://www.hankyung.com/2")]
    session.add_all(items)
    session.commit()

    summarize_and_store(session, FakeClient([reply(GOOD_SUMMARY), reply(GOOD_SUMMARY)]), items)

    rows = session.query(ApiUsage).filter_by(kind="summary").all()
    assert len(rows) == 2
    assert all(r.model == "claude-opus-5-5" and r.input_tokens == 100 for r in rows)
    session.close()

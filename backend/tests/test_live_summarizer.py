from __future__ import annotations

import os

import anthropic
import pytest

from app.config import get_settings
from app.db import init_db, make_engine, make_session_factory
from app.services.news_collector import collect_top_news
from app.services.summarizer import find_directive_phrases, paragraph_count, summarize_and_store

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(os.environ.get("RUN_LIVE") != "1", reason="RUN_LIVE=1일 때만 실행"),
]


def test_summarizes_five_real_news_items(tmp_path):
    settings = get_settings()
    engine = make_engine(f"sqlite:///{tmp_path / 'live.db'}")
    init_db(engine)
    session = make_session_factory(engine)()
    client = anthropic.Anthropic(api_key=settings.claude_api_key)

    try:
        items = collect_top_news(session, settings)
        summaries = summarize_and_store(session, client, items)
    finally:
        session.close()

    assert len(summaries) == 5
    for summary in summaries:
        assert 1 <= paragraph_count(summary.summary_text) <= 2
        assert find_directive_phrases(summary.summary_text) == []
        assert summary.hallucination_risk in {"low", "medium", "high"}


def test_generate_endpoint_end_to_end(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    from app.main import app

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'e2e.db'}")

    with TestClient(app) as client:
        response = client.post("/api/news/generate")

    assert response.status_code == 200
    body = response.json()
    items = body["news_items"]
    assert len(items) == 5
    assert paragraph_count(body["market_outlook"]) == 1
    assert len(body["investment_points"]) == 3
    assert find_directive_phrases(body["market_outlook"] + " ".join(body["investment_points"])) == []
    for item in items:
        assert set(item) == {"title", "source", "date", "url", "summary", "hallucination_risk"}
        assert 1 <= paragraph_count(item["summary"]) <= 2
        assert find_directive_phrases(item["summary"]) == []
        assert item["hallucination_risk"] in {"low", "medium", "high"}

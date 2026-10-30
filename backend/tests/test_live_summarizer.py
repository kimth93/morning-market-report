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

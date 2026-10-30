from __future__ import annotations

import os

import pytest

from app.config import get_settings
from app.db import init_db, make_engine, make_session_factory
from app.services.news_collector import collect_top_news

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(os.environ.get("RUN_LIVE") != "1", reason="RUN_LIVE=1일 때만 실행"),
]


def test_collects_five_real_news_items(tmp_path):
    settings = get_settings()
    engine = make_engine(f"sqlite:///{tmp_path / 'live.db'}")
    init_db(engine)
    session = make_session_factory(engine)()

    try:
        items = collect_top_news(session, settings)
    finally:
        session.close()

    assert len(items) == 5
    for item in items:
        assert item.title
        assert item.source
        assert item.date is not None
        assert item.url.startswith("http")

from __future__ import annotations

from datetime import date, datetime

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app.db import init_db, make_engine, make_session_factory
from app.models import NewsItem


@pytest.fixture
def engine(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    init_db(engine)
    return engine


def test_init_db_creates_three_tables(engine):
    tables = set(inspect(engine).get_table_names())

    assert {"news_items", "news_summaries", "email_subscribers"} <= tables


def test_duplicate_url_is_rejected(engine):
    session_factory = make_session_factory(engine)
    first = NewsItem(
        title="코스피 상승",
        source="한국경제",
        date=date(2026, 7, 8),
        url="https://example.com/a",
        collected_at=datetime(2026, 7, 8, 9, 0),
    )
    duplicate = NewsItem(
        title="코스피 상승 (중복)",
        source="한국경제",
        date=date(2026, 7, 8),
        url="https://example.com/a",
        collected_at=datetime(2026, 7, 8, 9, 0),
    )

    with session_factory() as session:
        session.add(first)
        session.commit()

    with session_factory() as session:
        session.add(duplicate)
        with pytest.raises(IntegrityError):
            session.commit()


def test_description_is_optional(engine):
    session_factory = make_session_factory(engine)
    item = NewsItem(
        title="환율 변동",
        source="연합뉴스",
        date=date(2026, 7, 8),
        url="https://example.com/b",
        collected_at=datetime(2026, 7, 8, 9, 0),
    )

    with session_factory() as session:
        session.add(item)
        session.commit()
        saved = session.query(NewsItem).filter_by(url="https://example.com/b").one()

    assert saved.description is None

from __future__ import annotations

import pytest

from app.collectors.naver_news import NaverAPIError
from app.config import Settings
from app.db import init_db, make_engine, make_session_factory
from app.models import NewsItem
from app.services.news_collector import collect_top_news


@pytest.fixture
def settings() -> Settings:
    return Settings(
        claude_api_key="test-claude-key",
        naver_client_id="test-naver-id",
        naver_client_secret="test-naver-secret",
        database_url="sqlite:///./app.db",
    )


@pytest.fixture
def session(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    init_db(engine)
    session = make_session_factory(engine)()
    yield session
    session.close()


def raw(title: str, url: str, pub_date: str, link: str = "https://n.news.naver.com/x") -> dict:
    return {
        "title": title,
        "originallink": url,
        "link": link,
        "description": "요약 문장",
        "pubDate": pub_date,
    }


def fake_fetch(results_by_keyword: dict[str, list[dict]]):
    def fetch(keyword, settings, sort="date", **kwargs):
        if isinstance(results_by_keyword[keyword], Exception):
            raise results_by_keyword[keyword]
        return results_by_keyword[keyword]

    return fetch


KEYWORDS = ["코스피", "환율"]


def test_same_article_from_two_keywords_is_saved_once(session, settings):
    shared = raw("<b>코스피</b> 상승", "https://www.hankyung.com/a", "Wed, 08 Jul 2026 09:00:00 +0900")
    fetch = fake_fetch({"코스피": [shared], "환율": [shared]})

    collect_top_news(session, settings, keywords=KEYWORDS, fetch=fetch)

    assert session.query(NewsItem).count() == 1


def test_empty_originallink_falls_back_to_link_and_empty_both_is_skipped(session, settings):
    fallback = raw("환율 변동", "", "Wed, 08 Jul 2026 09:00:00 +0900", link="https://n.news.naver.com/y")
    nothing = raw("빈 항목", "", "Wed, 08 Jul 2026 08:00:00 +0900", link="")
    fetch = fake_fetch({"코스피": [fallback, nothing], "환율": []})

    collect_top_news(session, settings, keywords=KEYWORDS, fetch=fetch)

    urls = [row.url for row in session.query(NewsItem).all()]
    assert urls == ["https://n.news.naver.com/y"]


def test_title_is_stored_without_markup(session, settings):
    item = raw("<b>코스피</b> &quot;상승&quot;", "https://www.hankyung.com/a", "Wed, 08 Jul 2026 09:00:00 +0900")
    fetch = fake_fetch({"코스피": [item], "환율": []})

    results = collect_top_news(session, settings, keywords=KEYWORDS, fetch=fetch)

    assert results[0].title == '코스피 "상승"'


def test_returns_newest_five_sorted_descending(session, settings):
    items = [
        raw(f"기사 {hour}", f"https://www.hankyung.com/{hour}", f"Wed, 08 Jul 2026 {hour:02d}:00:00 +0900")
        for hour in range(1, 8)
    ]
    fetch = fake_fetch({"코스피": items, "환율": []})

    results = collect_top_news(session, settings, keywords=KEYWORDS, fetch=fetch)

    assert len(results) == 5
    assert [r.title for r in results] == [f"기사 {h}" for h in range(7, 2, -1)]


def test_fewer_than_five_candidates_returns_what_exists(session, settings):
    items = [
        raw(f"기사 {hour}", f"https://www.hankyung.com/{hour}", f"Wed, 08 Jul 2026 {hour:02d}:00:00 +0900")
        for hour in range(1, 4)
    ]
    fetch = fake_fetch({"코스피": items, "환율": []})

    results = collect_top_news(session, settings, keywords=KEYWORDS, fetch=fetch)

    assert len(results) == 3


def test_already_saved_article_is_not_saved_again(session, settings):
    item = raw("코스피 상승", "https://www.hankyung.com/a", "Wed, 08 Jul 2026 09:00:00 +0900")
    fetch = fake_fetch({"코스피": [item], "환율": []})

    collect_top_news(session, settings, keywords=KEYWORDS, fetch=fetch)
    results = collect_top_news(session, settings, keywords=KEYWORDS, fetch=fetch)

    assert session.query(NewsItem).count() == 1
    assert len(results) == 1


def test_naver_error_propagates_and_saves_nothing(session, settings):
    item = raw("코스피 상승", "https://www.hankyung.com/a", "Wed, 08 Jul 2026 09:00:00 +0900")
    fetch = fake_fetch({"코스피": [item], "환율": NaverAPIError("rate limited", status_code=429)})

    with pytest.raises(NaverAPIError):
        collect_top_news(session, settings, keywords=KEYWORDS, fetch=fetch)

    assert session.query(NewsItem).count() == 0

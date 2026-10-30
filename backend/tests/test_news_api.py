from __future__ import annotations

from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient

from app.collectors.naver_news import NaverAPIError
from app.main import app
from app.models import NewsItem


@pytest.fixture(autouse=True)
def configured_env(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAUDE_API_KEY", "test-claude-key")
    monkeypatch.setenv("NAVER_CLIENT_ID", "test-naver-id")
    monkeypatch.setenv("NAVER_CLIENT_SECRET", "test-naver-secret")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")


def make_item(day: int, title: str | None = None) -> NewsItem:
    return NewsItem(
        title=title or f"기사 {day}",
        source="한국경제",
        date=date(2026, 7, day),
        url=f"https://www.hankyung.com/{day}",
        description="요약 문장",
        collected_at=datetime(2026, 7, 8, 9, 0),
    )


def test_collect_returns_items_with_required_fields(monkeypatch):
    def fake_collect(session, settings, **kwargs):
        return [make_item(8)]

    monkeypatch.setattr("app.api.news.collect_top_news", fake_collect)

    with TestClient(app) as client:
        response = client.post("/api/news/collect")

    assert response.status_code == 200
    body = response.json()
    assert "collected_at" in body
    assert len(body["news_items"]) == 1
    item = body["news_items"][0]
    assert item == {
        "title": "기사 8",
        "source": "한국경제",
        "date": "2026-07-08",
        "url": "https://www.hankyung.com/8",
        "description": "요약 문장",
    }


def test_collect_maps_naver_error_to_502(monkeypatch):
    def fake_collect(session, settings, **kwargs):
        raise NaverAPIError("네이버 API 오류 응답: 429", status_code=429)

    monkeypatch.setattr("app.api.news.collect_top_news", fake_collect)

    with TestClient(app) as client:
        response = client.post("/api/news/collect")

    assert response.status_code == 502
    assert response.json()["detail"] == "네이버 API 오류 응답: 429"


def test_latest_returns_five_newest_by_date(monkeypatch):
    with TestClient(app) as client:
        session = app.state.session_factory()
        session.add_all([make_item(day) for day in range(1, 8)])
        session.commit()
        session.close()

        response = client.get("/api/news/latest")

    assert response.status_code == 200
    dates = [item["date"] for item in response.json()["news_items"]]
    assert dates == ["2026-07-07", "2026-07-06", "2026-07-05", "2026-07-04", "2026-07-03"]

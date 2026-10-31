from __future__ import annotations

from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient

from app.collectors.naver_news import NaverAPIError
from app.main import app
from app.models import NewsItem
from app.services.outlook import Outlook


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


def make_summary(news_id: int, text: str = "요약 한 문단.", risk: str = "low"):
    from app.models import NewsSummary

    return NewsSummary(
        news_id=news_id,
        summary_text=text,
        hallucination_risk=risk,
        generated_at=datetime(2026, 7, 8, 9, 0),
    )


def test_generate_returns_items_with_summary_and_risk(monkeypatch):
    item = make_item(8)
    item.id = 1

    monkeypatch.setattr("app.services.report.claude_client", lambda settings: None)
    monkeypatch.setattr("app.services.report.collect_top_news", lambda session, settings, **kw: [item])
    monkeypatch.setattr(
        "app.services.report.summarize_and_store",
        lambda session, client, items: [make_summary(1, risk="medium")],
    )
    monkeypatch.setattr(
        "app.services.report.generate_outlook",
        lambda client, inputs: Outlook(market_outlook="전망 한 문단.", investment_points=["a", "b", "c"]),
    )

    with TestClient(app) as client:
        response = client.post("/api/news/generate")

    assert response.status_code == 200
    body = response.json()
    assert "generated_at" in body
    assert body["market_outlook"] == "전망 한 문단."
    assert body["investment_points"] == ["a", "b", "c"]
    assert body["news_items"] == [
        {
            "title": "기사 8",
            "source": "한국경제",
            "date": "2026-07-08",
            "url": "https://www.hankyung.com/8",
            "summary": "요약 한 문단.",
            "hallucination_risk": "medium",
        }
    ]


def test_generate_maps_naver_error_to_502(monkeypatch):
    def fail(session, settings, **kw):
        raise NaverAPIError("네이버 API 오류 응답: 429", status_code=429)

    monkeypatch.setattr("app.services.report.claude_client", lambda settings: None)
    monkeypatch.setattr("app.services.report.collect_top_news", fail)

    with TestClient(app) as client:
        response = client.post("/api/news/generate")

    assert response.status_code == 502


def test_generate_maps_summary_error_to_502(monkeypatch):
    from app.services.summarizer import SummaryError

    item = make_item(8)
    item.id = 1

    def fail(session, client, items):
        raise SummaryError("요약 검증 실패: 문단 수")

    monkeypatch.setattr("app.services.report.claude_client", lambda settings: None)
    monkeypatch.setattr("app.services.report.collect_top_news", lambda session, settings, **kw: [item])
    monkeypatch.setattr("app.services.report.summarize_and_store", fail)

    with TestClient(app) as client:
        response = client.post("/api/news/generate")

    assert response.status_code == 502
    assert "요약 검증 실패" in response.json()["detail"]


def test_generate_maps_outlook_error_to_502(monkeypatch):
    from app.services.outlook import OutlookError

    item = make_item(8)
    item.id = 1

    def fail(client, inputs):
        raise OutlookError("전망 검증 실패: 투자포인트 개수 2")

    monkeypatch.setattr("app.services.report.claude_client", lambda settings: None)
    monkeypatch.setattr("app.services.report.collect_top_news", lambda session, settings, **kw: [item])
    monkeypatch.setattr(
        "app.services.report.summarize_and_store",
        lambda session, client, items: [make_summary(1)],
    )
    monkeypatch.setattr("app.services.report.generate_outlook", fail)

    with TestClient(app) as client:
        response = client.post("/api/news/generate")

    assert response.status_code == 502
    assert "전망 검증 실패" in response.json()["detail"]

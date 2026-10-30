from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import anthropic
from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select

from app.collectors.naver_news import NaverAPIError
from app.config import get_settings
from app.models import NewsItem, NewsSummary
from app.services.news_collector import collect_top_news
from app.services.outlook import Outlook, OutlookError, generate_outlook
from app.services.summarizer import SummaryError, summarize_and_store

router = APIRouter(prefix="/api/news", tags=["news"])
LATEST_LIMIT = 5


def _serialize(item: NewsItem) -> dict[str, Any]:
    return {
        "title": item.title,
        "source": item.source,
        "date": item.date.isoformat(),
        "url": item.url,
        "description": item.description,
    }


@router.post("/collect")
def collect(request: Request) -> dict[str, Any]:
    settings = get_settings()
    session = request.app.state.session_factory()
    try:
        try:
            items = collect_top_news(session, settings)
        except NaverAPIError as exc:
            raise HTTPException(status_code=502, detail=exc.message) from exc
        return {
            "news_items": [_serialize(item) for item in items],
            "collected_at": datetime.now(timezone.utc).isoformat(),
        }
    finally:
        session.close()


@router.get("/latest")
def latest(request: Request) -> dict[str, Any]:
    session = request.app.state.session_factory()
    try:
        rows = session.scalars(
            select(NewsItem)
            .order_by(NewsItem.date.desc(), NewsItem.collected_at.desc())
            .limit(LATEST_LIMIT)
        ).all()
        return {"news_items": [_serialize(item) for item in rows]}
    finally:
        session.close()


def _claude_client(settings: Any) -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=settings.claude_api_key)


@router.post("/generate")
def generate(request: Request) -> dict[str, Any]:
    settings = get_settings()
    session = request.app.state.session_factory()
    try:
        try:
            items = collect_top_news(session, settings)
            client = _claude_client(settings)
            summaries = summarize_and_store(session, client, items)
            summary_by_news_id = {summary.news_id: summary for summary in summaries}
            outlook = generate_outlook(
                client,
                [(item.title, summary_by_news_id[item.id].summary_text) for item in items],
            )
        except (NaverAPIError, SummaryError, OutlookError, anthropic.APIError) as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        return {
            "news_items": [
                _serialize_with_summary(item, summary_by_news_id[item.id]) for item in items
            ],
            "market_outlook": outlook.market_outlook,
            "investment_points": outlook.investment_points,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    finally:
        session.close()


def _serialize_with_summary(item: NewsItem, summary: NewsSummary) -> dict[str, Any]:
    return {
        "title": item.title,
        "source": item.source,
        "date": item.date.isoformat(),
        "url": item.url,
        "summary": summary.summary_text,
        "hallucination_risk": summary.hallucination_risk,
    }

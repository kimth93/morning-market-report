from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select

from app.collectors.naver_news import NaverAPIError
from app.config import get_settings
from app.models import NewsItem
from app.services.news_collector import collect_top_news

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

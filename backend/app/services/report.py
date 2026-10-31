from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

import anthropic
from sqlalchemy.orm import Session

from app.collectors.naver_news import NaverAPIError
from app.services.news_collector import collect_top_news
from app.services.outlook import generate_outlook
from app.services.summarizer import summarize_and_store
from app.services.usage import record_usage
from app.config import Settings
from app.models import NewsItem
from app.services.outlook import MODEL as OUTLOOK_MODEL


def claude_client(settings: Settings) -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=settings.claude_api_key)


def serialize_item(item: NewsItem, summary_text: str, risk: str) -> dict[str, Any]:
    return {
        "title": item.title,
        "source": item.source,
        "date": item.date.isoformat(),
        "url": item.url,
        "summary": summary_text,
        "hallucination_risk": risk,
    }


def generate_report(session: Session, settings: Settings, client: Optional[Any] = None) -> dict[str, Any]:
    """뉴스 수집, 요약, 전망 생성을 한 번에 수행한다. 실패 예외는 호출하는 쪽에서 처리한다."""
    client = client or claude_client(settings)
    items = collect_top_news(session, settings)
    summaries = summarize_and_store(session, client, items)
    summary_by_news_id = {summary.news_id: summary for summary in summaries}
    outlook = generate_outlook(
        client,
        [(item.title, summary_by_news_id[item.id].summary_text) for item in items],
    )
    record_usage(
        session,
        kind="outlook",
        model=OUTLOOK_MODEL,
        input_tokens=outlook.input_tokens,
        output_tokens=outlook.output_tokens,
    )
    session.commit()

    return {
        "news_items": [
            serialize_item(item, summary_by_news_id[item.id].summary_text, summary_by_news_id[item.id].hallucination_risk)
            for item in items
        ],
        "market_outlook": outlook.market_outlook,
        "investment_points": outlook.investment_points,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


__all__ = ["NaverAPIError", "generate_report", "claude_client", "serialize_item"]

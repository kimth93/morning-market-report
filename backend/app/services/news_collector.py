from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Optional

from sqlalchemy.orm import Session

from app.collectors.keywords import KEYWORDS
from app.collectors.naver_news import fetch_news
from app.collectors.normalize import (
    parse_pub_date,
    press_name,
    strip_markup,
    to_kst_date,
)
from app.config import Settings
from app.models import NewsItem


def collect_top_news(
    session: Session,
    settings: Settings,
    keywords: list[str] = KEYWORDS,
    limit: int = 5,
    fetch: Callable[..., list[dict]] = fetch_news,
) -> list[NewsItem]:
    candidates: dict[str, dict[str, Any]] = {}
    for keyword in keywords:
        for raw in fetch(keyword, settings, sort="date"):
            candidate = _normalize(raw)
            if candidate is None or candidate["url"] in candidates:
                continue
            candidates[candidate["url"]] = candidate

    selected = sorted(candidates.values(), key=lambda c: c["published_at"], reverse=True)[:limit]

    collected_at = datetime.now(timezone.utc).replace(tzinfo=None)
    results: list[NewsItem] = []
    for candidate in selected:
        item = session.query(NewsItem).filter_by(url=candidate["url"]).one_or_none()
        if item is None:
            item = NewsItem(
                title=candidate["title"],
                source=candidate["source"],
                date=candidate["date"],
                url=candidate["url"],
                description=candidate["description"],
                collected_at=collected_at,
            )
            session.add(item)
        results.append(item)

    session.commit()
    return results


def _normalize(raw: dict[str, Any]) -> Optional[dict[str, Any]]:
    url = raw.get("originallink") or raw.get("link")
    if not url:
        return None

    published_at = parse_pub_date(raw["pubDate"])
    return {
        "title": strip_markup(raw["title"]),
        "source": press_name(url),
        "date": to_kst_date(published_at),
        "url": url,
        "description": strip_markup(raw.get("description", "")) or None,
        "published_at": published_at,
    }

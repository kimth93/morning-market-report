from __future__ import annotations

import datetime as dt
from collections import defaultdict
from typing import Any, Literal, Optional

from sqlalchemy.orm import Session

from app.models import ApiUsage

# 모델별 USD 가격 (100만 토큰당, 입력/출력). Claude API 가격 문서의 캐시 표 기준이므로 시연 전 다시 확인한다.
PRICES_PER_MTOK: dict[str, tuple[float, float]] = {
    "claude-opus-5-5": (4.00, 20.00),
}
PRICING_NOTE = "추정 비용입니다. 가격은 Claude API 가격 문서(캐시 기준)를 따르며 실제 청구와 다를 수 있습니다."

Period = Literal["daily", "monthly"]


def record_usage(
    session: Session,
    kind: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    now: Optional[dt.datetime] = None,
) -> None:
    created_at = now or dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    session.add(
        ApiUsage(
            kind=kind,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            created_at=created_at,
        )
    )


def aggregate_usage(session: Session, period: Period) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = defaultdict(
        lambda: {"calls": 0, "input_tokens": 0, "output_tokens": 0}
    )
    for row in session.query(ApiUsage).all():
        key_date = row.created_at.date().isoformat() if period == "daily" else row.created_at.strftime("%Y-%m")
        bucket = grouped[(key_date, row.model)]
        bucket["calls"] += 1
        bucket["input_tokens"] += row.input_tokens
        bucket["output_tokens"] += row.output_tokens

    rows = []
    for (period_key, model), bucket in sorted(grouped.items()):
        rows.append(
            {
                "period": period_key,
                "model": model,
                **bucket,
                "estimated_cost_usd": _estimate_cost(model, bucket["input_tokens"], bucket["output_tokens"]),
            }
        )
    return rows


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> Optional[float]:
    price = PRICES_PER_MTOK.get(model)
    if price is None:
        return None
    input_price, output_price = price
    cost = input_tokens / 1_000_000 * input_price + output_tokens / 1_000_000 * output_price
    return round(cost, 6)

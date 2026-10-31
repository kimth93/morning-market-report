from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Query, Request

from app.services.usage import PRICING_NOTE, aggregate_usage

router = APIRouter(prefix="/api/usage", tags=["usage"])


@router.get("")
def usage(request: Request, period: Literal["daily", "monthly"] = Query(default="daily")) -> dict[str, Any]:
    session = request.app.state.session_factory()
    try:
        return {"period": period, "rows": aggregate_usage(session, period), "pricing_note": PRICING_NOTE}
    finally:
        session.close()

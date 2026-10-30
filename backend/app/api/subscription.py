from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from app.models import EmailSubscriber

router = APIRouter(prefix="/api/subscription", tags=["subscription"])

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SignupRequest(BaseModel):
    email: str = Field(max_length=254)
    name: str = Field(min_length=1, max_length=100)

    @field_validator("email")
    @classmethod
    def email_must_look_valid(cls, value: str) -> str:
        if not _EMAIL_PATTERN.match(value):
            raise ValueError("이메일 형식이 올바르지 않습니다")
        return value


@router.post("/signup")
def signup(payload: SignupRequest, request: Request) -> dict[str, Any]:
    # 실제 발송은 v2 범위이므로 이메일 주소와 이름만 저장한다.
    session = request.app.state.session_factory()
    try:
        row = EmailSubscriber(
            email=payload.email,
            name=payload.name,
            subscribed_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        session.add(row)
        session.commit()
        return {"status": "success", "subscription_id": str(row.id)}
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail="구독 신청을 저장하지 못했습니다") from exc
    finally:
        session.close()

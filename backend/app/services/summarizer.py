from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

from sqlalchemy.orm import Session

from app.models import NewsItem, NewsSummary

MODEL = "claude-opus-5-5"
MAX_TOKENS = 2000
MAX_ATTEMPTS = 2
MIN_PARAGRAPHS = 1
MAX_PARAGRAPHS = 2
RISK_LEVELS = ["low", "medium", "high"]
DIRECTIVE_PHRASES = ["사세요", "파세요", "매수하", "매도하", "반드시", "사야", "추천합니다", "상승한다", "하락한다"]

SYSTEM_PROMPT = """당신은 금융뉴스 요약 전문가입니다.
- 원문에 있는 정보만 요약하세요. 원문에 없는 수치나 통계를 만들지 마세요 (할루시네이션 금지).
- "반드시", "사세요", "상승한다" 같은 직접 투자 권유나 단정 표현은 쓰지 마세요.
- "~할 가능성이 있다", "~는 주목할 만하다" 같은 조건부 표현만 사용하세요.
- 원뉴스의 톤과 균형을 유지하세요.
- 요약은 1~2문단으로 작성하고, 문단 사이는 빈 줄로 구분하세요.
- hallucination_risk에는 요약이 원문을 얼마나 벗어날 위험이 있는지를 low, medium, high 중 하나로 적으세요."""

SUMMARY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "hallucination_risk": {"type": "string", "enum": RISK_LEVELS},
    },
    "required": ["summary", "hallucination_risk"],
    "additionalProperties": False,
}


class SummaryError(Exception):
    pass


@dataclass(frozen=True)
class Summary:
    text: str
    hallucination_risk: str


def find_directive_phrases(text: str) -> list[str]:
    return [phrase for phrase in DIRECTIVE_PHRASES if phrase in text]


def paragraph_count(text: str) -> int:
    return len([part for part in text.split("\n\n") if part.strip()])


def summarize_news(client: Any, item: NewsItem) -> Summary:
    problem = ""
    for _ in range(MAX_ATTEMPTS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            output_config={"effort": "medium", "format": {"type": "json_schema", "schema": SUMMARY_SCHEMA}},
            messages=[{"role": "user", "content": _user_message(item)}],
        )
        if response.stop_reason == "refusal":
            raise SummaryError("모델이 요약을 거부했습니다")

        text_block = next(block for block in response.content if block.type == "text")
        data = json.loads(text_block.text)
        summary = data["summary"].strip()

        problems = []
        if not MIN_PARAGRAPHS <= paragraph_count(summary) <= MAX_PARAGRAPHS:
            problems.append("문단 수")
        directives = find_directive_phrases(summary)
        if directives:
            problems.append("투자 권유 표현: " + ", ".join(directives))
        if not problems:
            return Summary(text=summary, hallucination_risk=data["hallucination_risk"])
        problem = "; ".join(problems)

    raise SummaryError(f"요약 검증 실패: {problem}")


def summarize_and_store(session: Session, client: Any, items: Iterable[NewsItem]) -> list[NewsSummary]:
    results: list[NewsSummary] = []
    for item in items:
        existing = session.query(NewsSummary).filter_by(news_id=item.id).one_or_none()
        if existing is not None:
            results.append(existing)
            continue

        summary = summarize_news(client, item)
        row = NewsSummary(
            news_id=item.id,
            summary_text=summary.text,
            hallucination_risk=summary.hallucination_risk,
            generated_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        session.add(row)
        results.append(row)

    session.commit()
    return results


def _user_message(item: NewsItem) -> str:
    return (
        f"제목: {item.title}\n"
        f"언론사: {item.source}\n"
        f"발행일: {item.date.isoformat()}\n"
        f"네이버 제공 기사 요약: {item.description or '(없음)'}\n\n"
        "위 정보만 사용해 기사를 요약하세요."
    )

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Sequence

from app.services.summarizer import (
    MAX_TOKENS,
    MODEL,
    find_directive_phrases,
    paragraph_count,
)

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 2
POINT_COUNT = 3
MAX_LINES_PER_POINT = 2
MAX_OUTLOOK_CHARS = 400

SYSTEM_PROMPT = """당신은 금융시장 분석 보조자입니다.
- 제공된 뉴스 요약에 있는 내용만 바탕으로 작성하세요. 없는 수치나 사실을 만들지 마세요 (할루시네이션 금지).
- "반드시", "사세요", "상승한다" 같은 단정이나 직접 투자 권유는 쓰지 마세요.
- "~할 가능성이 있다", "~는 주목할 만하다" 같은 조건부 표현만 사용하세요.
- 뉴스 사이의 인과관계는 요약이 명시한 경우에만 언급하세요. 관련이 약한 개별 기업 실적을 시장 흐름과 억지로 엮지 마세요.
- 전망에 쓰는 수치는 핵심 3개 이내로 줄이세요.
- 특정 종목이나 섹터를 과도하게 강조하지 말고, 뉴스에 나온 여러 흐름을 균형 있게 다루세요.

출력:
- market_outlook: 오늘의 시장 전망을 1문단, 3~4문장, 400자 이내로 작성하세요.
- investment_points: 주목할 투자포인트를 정확히 3개, 각각 1~2줄로 작성하세요. 투자 권유가 아니라 관찰할 지점으로 표현하세요. 서로 다른 흐름을 다루도록 하세요."""

OUTLOOK_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "market_outlook": {"type": "string"},
        "investment_points": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["market_outlook", "investment_points"],
    "additionalProperties": False,
}


class OutlookError(Exception):
    pass


@dataclass(frozen=True)
class Outlook:
    market_outlook: str
    investment_points: list[str] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0


def generate_outlook(client: Any, inputs: Sequence[tuple[str, str]]) -> Outlook:
    """inputs: (기사 제목, 요약 본문) 쌍. 뉴스 요약만 근거로 전망과 투자포인트를 만든다."""
    problem = ""
    input_tokens = 0
    output_tokens = 0
    for _ in range(MAX_ATTEMPTS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            output_config={"effort": "medium", "format": {"type": "json_schema", "schema": OUTLOOK_SCHEMA}},
            messages=[{"role": "user", "content": _user_message(inputs)}],
        )
        usage = getattr(response, "usage", None)
        input_tokens += getattr(usage, "input_tokens", 0)
        output_tokens += getattr(usage, "output_tokens", 0)
        if response.stop_reason == "refusal":
            raise OutlookError("모델이 전망 생성을 거부했습니다")

        text_block = next(block for block in response.content if block.type == "text")
        data = json.loads(text_block.text)
        outlook = data["market_outlook"].strip()
        points = [point.strip() for point in data["investment_points"]]

        problems = _validate(outlook, points)
        if not problems:
            logger.info(
                "outlook model=%s input_tokens=%s output_tokens=%s",
                MODEL,
                input_tokens,
                output_tokens,
            )
            return Outlook(
                market_outlook=outlook,
                investment_points=points,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
        problem = "; ".join(problems)

    raise OutlookError(f"전망 검증 실패: {problem}")


def _validate(outlook: str, points: list[str]) -> list[str]:
    problems = []
    if paragraph_count(outlook) != 1:
        problems.append("시장 전망 문단 수")
    if len(outlook) > MAX_OUTLOOK_CHARS:
        problems.append(f"시장 전망 길이 {len(outlook)}자")
    if len(points) != POINT_COUNT:
        problems.append(f"투자포인트 개수 {len(points)}")
    if any(not point or point.count("\n") + 1 > MAX_LINES_PER_POINT for point in points):
        problems.append("투자포인트 줄 수")
    directives = find_directive_phrases(" ".join([outlook, *points]))
    if directives:
        problems.append("투자 권유 표현: " + ", ".join(directives))
    return problems


def _user_message(inputs: Sequence[tuple[str, str]]) -> str:
    lines = [f"{index}. 제목: {title}\n   요약: {summary}" for index, (title, summary) in enumerate(inputs, start=1)]
    return "오늘 수집된 뉴스 요약입니다.\n\n" + "\n".join(lines) + "\n\n위 요약만 근거로 작성하세요."

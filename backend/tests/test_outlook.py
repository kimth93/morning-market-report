from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from app.services.outlook import MODEL, OutlookError, generate_outlook

OUTLOOK = "반도체 업종의 약세가 이어질 가능성이 있어 주목할 만합니다."
POINTS = ["반도체 업종 변동성 확인", "환율과 금리 발표 일정 체크", "실적 발표 후 수급 흐름 관찰"]
INPUTS = [("코스피 급락", "코스피가 3.48% 하락해 마감했습니다."), ("환율 변동", "원·달러 환율이 올랐습니다.")]


class FakeMessages:
    def __init__(self, replies: list[str]):
        self.replies = list(replies)
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            stop_reason="end_turn",
            content=[SimpleNamespace(type="text", text=self.replies.pop(0))],
            usage=SimpleNamespace(input_tokens=50, output_tokens=30),
        )


class FakeClient:
    def __init__(self, replies: list[str]):
        self.messages = FakeMessages(replies)


def reply(outlook: str = OUTLOOK, points: list[str] | None = None) -> str:
    return json.dumps(
        {"market_outlook": outlook, "investment_points": points if points is not None else POINTS},
        ensure_ascii=False,
    )


def test_request_uses_opus_schema_and_reliability_rules():
    client = FakeClient([reply()])

    generate_outlook(client, INPUTS)

    call = client.messages.calls[0]
    assert call["model"] == MODEL == "claude-opus-5-5"
    assert call["output_config"]["format"]["type"] == "json_schema"
    assert "할루시네이션" in call["system"]


def test_user_message_contains_every_title_and_summary():
    client = FakeClient([reply()])

    generate_outlook(client, INPUTS)

    content = client.messages.calls[0]["messages"][0]["content"]
    for title, summary in INPUTS:
        assert title in content
        assert summary in content


def test_returns_outlook_and_three_points_with_token_usage():
    client = FakeClient([reply()])

    result = generate_outlook(client, INPUTS)

    assert result.market_outlook == OUTLOOK
    assert result.investment_points == POINTS
    assert result.input_tokens == 50
    assert result.output_tokens == 30


def test_retries_when_point_count_is_not_three():
    client = FakeClient([reply(points=POINTS[:2]), reply()])

    result = generate_outlook(client, INPUTS)

    assert len(result.investment_points) == 3
    assert len(client.messages.calls) == 2


def test_retries_when_a_point_contains_directive():
    client = FakeClient([reply(points=["반도체를 반드시 사세요", POINTS[1], POINTS[2]]), reply()])

    result = generate_outlook(client, INPUTS)

    assert result.investment_points == POINTS


def test_retries_when_outlook_is_not_one_paragraph():
    two = "첫 문단입니다.\n\n둘째 문단입니다."
    client = FakeClient([reply(outlook=two), reply()])

    result = generate_outlook(client, INPUTS)

    assert result.market_outlook == OUTLOOK


def test_repeated_violation_raises_outlook_error():
    client = FakeClient([reply(points=POINTS[:2]), reply(points=POINTS[:2])])

    with pytest.raises(OutlookError):
        generate_outlook(client, INPUTS)


def test_retries_when_outlook_is_too_long():
    long_outlook = "가" * 401
    client = FakeClient([reply(outlook=long_outlook), reply()])

    result = generate_outlook(client, INPUTS)

    assert result.market_outlook == OUTLOOK

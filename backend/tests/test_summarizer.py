from __future__ import annotations

import json
from datetime import date, datetime
from types import SimpleNamespace

import pytest

from app.db import init_db, make_engine, make_session_factory
from app.models import NewsItem, NewsSummary
from app.services.summarizer import (
    MODEL,
    SummaryError,
    find_directive_phrases,
    paragraph_count,
    summarize_and_store,
    summarize_news,
)

GOOD_SUMMARY = "코스피가 3.48% 하락해 마감했습니다.\n\n반도체 업종의 하락 폭이 컸다는 보도가 있습니다."


class FakeMessages:
    def __init__(self, replies: list[str], stop_reason: str = "end_turn"):
        self.replies = list(replies)
        self.stop_reason = stop_reason
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        text = self.replies.pop(0)
        return SimpleNamespace(
            stop_reason=self.stop_reason,
            content=[SimpleNamespace(type="text", text=text)],
            usage=SimpleNamespace(input_tokens=100, output_tokens=40),
        )


class FakeClient:
    def __init__(self, replies: list[str], stop_reason: str = "end_turn"):
        self.messages = FakeMessages(replies, stop_reason)


def reply(summary: str, risk: str = "low") -> str:
    return json.dumps({"summary": summary, "hallucination_risk": risk}, ensure_ascii=False)


def news(title: str = "코스피 급락", url: str = "https://www.hankyung.com/a") -> NewsItem:
    return NewsItem(
        title=title,
        source="한국경제",
        date=date(2026, 7, 8),
        url=url,
        description="코스피가 3.48% 내린 채 마감했습니다.",
        collected_at=datetime(2026, 7, 8, 9, 0),
    )


def test_request_uses_opus_json_schema_and_reliability_rules():
    client = FakeClient([reply(GOOD_SUMMARY)])

    summarize_news(client, news())

    call = client.messages.calls[0]
    assert call["model"] == MODEL == "claude-opus-5-5"
    assert call["output_config"]["format"]["type"] == "json_schema"
    assert "할루시네이션" in call["system"]


def test_returns_summary_text_and_risk():
    client = FakeClient([reply(GOOD_SUMMARY, risk="medium")])

    result = summarize_news(client, news())

    assert result.text == GOOD_SUMMARY
    assert result.hallucination_risk == "medium"


def test_retries_when_investment_directive_appears():
    directive = "이 주식을 사세요.\n\n추가 정보는 없습니다."
    client = FakeClient([reply(directive), reply(GOOD_SUMMARY)])

    result = summarize_news(client, news())

    assert result.text == GOOD_SUMMARY
    assert len(client.messages.calls) == 2


def test_retries_when_paragraph_count_is_out_of_range():
    three = "문단 하나.\n\n문단 둘.\n\n문단 셋."
    client = FakeClient([reply(three), reply(GOOD_SUMMARY)])

    result = summarize_news(client, news())

    assert result.text == GOOD_SUMMARY


def test_repeated_violation_raises_summary_error():
    directive = "이 주식을 사세요."
    client = FakeClient([reply(directive), reply(directive)])

    with pytest.raises(SummaryError):
        summarize_news(client, news())


def test_refusal_raises_summary_error():
    client = FakeClient([reply(GOOD_SUMMARY)], stop_reason="refusal")

    with pytest.raises(SummaryError):
        summarize_news(client, news())


def test_summary_reports_token_usage_across_attempts():
    directive = "이 주식을 사세요."
    client = FakeClient([reply(directive), reply(GOOD_SUMMARY)])

    result = summarize_news(client, news())

    assert result.input_tokens == 200
    assert result.output_tokens == 80


def test_detects_directive_phrases_and_counts_paragraphs():
    assert find_directive_phrases("반드시 매수하세요") != []
    assert find_directive_phrases("주목할 만한 흐름이 보입니다") == []
    assert paragraph_count("가.\n\n나.") == 2


@pytest.fixture
def session(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    init_db(engine)
    session = make_session_factory(engine)()
    yield session
    session.close()


def test_store_saves_one_summary_per_news_item(session):
    items = [news("기사 1", "https://www.hankyung.com/1"), news("기사 2", "https://www.hankyung.com/2")]
    session.add_all(items)
    session.commit()
    client = FakeClient([reply(GOOD_SUMMARY), reply(GOOD_SUMMARY, risk="high")])

    summarize_and_store(session, client, items)

    rows = session.query(NewsSummary).order_by(NewsSummary.news_id).all()
    assert [r.news_id for r in rows] == [items[0].id, items[1].id]
    assert rows[1].hallucination_risk == "high"


def test_store_skips_news_that_already_has_a_summary(session):
    item = news()
    session.add(item)
    session.commit()
    first = FakeClient([reply(GOOD_SUMMARY)])
    summarize_and_store(session, first, [item])

    second = FakeClient([])
    summarize_and_store(session, second, [item])

    assert second.messages.calls == []
    assert session.query(NewsSummary).count() == 1

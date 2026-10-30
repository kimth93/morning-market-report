from __future__ import annotations

from app.services.reliability import check_report, classify_sector

GOOD_ITEM = {
    "title": "코스피 상승",
    "source": "한국경제",
    "date": "2026-07-08",
    "url": "https://www.hankyung.com/a",
    "summary": "코스피가 올랐다. 주목할 만한 흐름이다.",
    "hallucination_risk": "low",
}


def report(**overrides):
    base = {
        "news_items": [GOOD_ITEM],
        "market_outlook": "반도체 흐름이 이어질 가능성이 있습니다.",
        "investment_points": ["환율 변동을 지켜볼 필요가 있다", "금리 발표 일정 확인", "실적 발표 흐름 관찰"],
    }
    base.update(overrides)
    return base


def test_clean_report_passes_all_checks():
    findings = check_report(report())

    assert [f for f in findings if f.level == "fail"] == []


def test_missing_source_field_fails():
    item = {**GOOD_ITEM, "url": ""}

    findings = check_report(report(news_items=[item]))

    assert any(f.level == "fail" and "출처" in f.message for f in findings)


def test_directive_phrase_anywhere_fails():
    findings = check_report(report(investment_points=["이 주식을 사세요", "b", "c"]))

    assert any(f.level == "fail" and "투자 권유" in f.message for f in findings)


def test_outlook_without_conditional_expression_warns():
    findings = check_report(report(market_outlook="코스피가 3% 하락했다."))

    assert any(f.level == "warn" and "조건부" in f.message for f in findings)


def test_sector_concentration_warns_when_one_sector_dominates():
    tech = {**GOOD_ITEM, "title": "반도체 실적 호조", "summary": "반도체 업종이 강세다."}
    items = [tech] * 4 + [{**GOOD_ITEM, "title": "금리 동결", "summary": "금리가 동결됐다."}]

    findings = check_report(report(news_items=items))

    assert any(f.level == "warn" and "IT" in f.message for f in findings)


def test_classify_sector_uses_keywords():
    assert classify_sector("반도체 업황 개선") == "IT"
    assert classify_sector("기준금리 동결") == "금융"
    assert classify_sector("신약 임상 결과") == "바이오"
    assert classify_sector("국제 유가 급등") == "에너지"
    assert classify_sector("날씨 소식") == "기타"

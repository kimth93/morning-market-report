from __future__ import annotations

from datetime import date

from app.collectors.normalize import (
    parse_pub_date,
    press_name,
    strip_markup,
    to_kst_date,
)


def test_strip_markup_removes_tags_and_unescapes_entities():
    raw = "<b>삼성</b>&quot;주가&quot; &amp; 환율"

    assert strip_markup(raw) == '삼성"주가" & 환율'


def test_parse_pub_date_keeps_timezone():
    parsed = parse_pub_date("Wed, 08 Jul 2026 00:30:00 +0900")

    assert parsed.tzinfo is not None


def test_kst_date_for_kst_morning_article():
    parsed = parse_pub_date("Wed, 08 Jul 2026 00:30:00 +0900")

    assert to_kst_date(parsed) == date(2026, 7, 8)


def test_kst_date_rolls_over_from_utc_afternoon():
    # UTC 2026-07-07 15:30 is KST 2026-07-08 00:30
    parsed = parse_pub_date("Tue, 07 Jul 2026 15:30:00 +0000")

    assert to_kst_date(parsed) == date(2026, 7, 8)


def test_press_name_maps_known_domain_ignoring_www():
    assert press_name("https://www.hankyung.com/economy/article/1") == "한국경제"


def test_press_name_falls_back_to_domain_when_unknown():
    assert press_name("https://www.unknown-site.example/news/1") == "unknown-site.example"


def test_press_name_matches_subdomain_of_known_outlet():
    assert press_name("https://news.einfomax.co.kr/news/articleView.html?idxno=1") == "연합인포맥스"


def test_press_name_prefers_most_specific_domain():
    assert press_name("https://biz.chosun.com/international/1") == "조선비즈"
    assert press_name("https://www.chosun.com/economy/1") == "조선일보"


def test_press_name_does_not_match_lookalike_domain():
    assert press_name("https://notmk.co.kr/x") == "notmk.co.kr"


def test_press_map_entries_are_clean_domains_and_names():
    from app.collectors.press_map import PRESS_BY_DOMAIN

    assert len(PRESS_BY_DOMAIN) >= 20
    for domain, name in PRESS_BY_DOMAIN.items():
        assert "/" not in domain and not domain.startswith("www.")
        assert name.strip() == name and name

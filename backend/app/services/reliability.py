from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.outlook import POINT_COUNT
from app.services.summarizer import find_directive_phrases

CONDITIONAL_MARKERS = ["가능성", "주목", "보입니다", "보인", "지켜볼", "관찰", "확인해 볼", "필요가 있"]
SECTOR_KEYWORDS: dict[str, list[str]] = {
    "IT": ["반도체", "AI", "인공지능", "기술주", "엔비디아", "인텔", "소프트웨어", "플랫폼"],
    "금융": ["금리", "환율", "은행", "채권", "증시", "코스피", "코스닥", "달러", "증권"],
    "바이오": ["바이오", "제약", "임상", "신약"],
    "에너지": ["유가", "에너지", "원유", "석유", "전력", "원자재"],
    "자동차": ["자동차", "기아", "현대차", "모빌리티"],
}
MAX_SHARE_OF_ONE_SECTOR = 0.6  # 5건 중 3건을 넘으면 한 섹터 쏠림으로 본다.


@dataclass(frozen=True)
class Finding:
    level: str  # "ok" | "warn" | "fail"
    message: str


def classify_sector(text: str) -> str:
    for sector, keywords in SECTOR_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return sector
    return "기타"


def check_report(payload: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    items = payload.get("news_items", [])
    outlook = payload.get("market_outlook", "")
    points = payload.get("investment_points", [])

    # 출처 명시: 모든 뉴스에 제목, 언론사, 발행일, 링크가 있어야 한다.
    missing = [
        item.get("title", "(제목 없음)")
        for item in items
        if not all(item.get(field) for field in ("title", "source", "date", "url"))
    ]
    if missing:
        findings.append(Finding("fail", f"출처 필드 누락: {len(missing)}건"))
    else:
        findings.append(Finding("ok", "모든 뉴스에 출처 필드가 있습니다"))

    # 단정성: 투자 권유 표현이 한 곳이라도 있으면 실패다.
    all_text = " ".join([outlook, *points, *(item.get("summary", "") for item in items)])
    directives = find_directive_phrases(all_text)
    if directives:
        findings.append(Finding("fail", "투자 권유 표현: " + ", ".join(directives)))
    else:
        findings.append(Finding("ok", "투자 권유 표현이 없습니다"))

    # 조건부 표현: 전망 문단에 조건부 표현이 있어야 한다.
    if any(marker in outlook for marker in CONDITIONAL_MARKERS):
        findings.append(Finding("ok", "전망에 조건부 표현이 있습니다"))
    else:
        findings.append(Finding("warn", "전망에 조건부 표현이 없습니다"))

    if len(points) != POINT_COUNT:
        findings.append(Finding("fail", f"투자포인트 개수 {len(points)}"))

    # 편향성: 한 섹터가 기사 대부분을 차지하면 경고한다.
    sectors = [classify_sector(f"{item.get('title', '')} {item.get('summary', '')}") for item in items]
    if sectors:
        top_sector, top_count = max(((s, sectors.count(s)) for s in set(sectors)), key=lambda pair: pair[1])
        if top_count / len(sectors) > MAX_SHARE_OF_ONE_SECTOR:
            findings.append(Finding("warn", f"{top_sector} 섹터 쏠림: {top_count}/{len(sectors)}건"))
        else:
            findings.append(Finding("ok", "섹터 분포가 한쪽으로 치우치지 않습니다"))

    return findings

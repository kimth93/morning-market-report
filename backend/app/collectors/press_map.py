from __future__ import annotations

# 원문 도메인 -> 언론사명. www.은 떼고 적는다. 하위 도메인은 가장 긴 일치 규칙으로 찾는다
# (예: biz.chosun.com은 조선비즈, www.chosun.com은 조선일보).
# 확실하지 않은 도메인은 넣지 않는다. 빠진 언론사는 도메인 문자열로 표시된다.
PRESS_BY_DOMAIN: dict[str, str] = {
    "hankyung.com": "한국경제",
    "mk.co.kr": "매일경제",
    "yna.co.kr": "연합뉴스",
    "sedaily.com": "서울경제",
    "biz.chosun.com": "조선비즈",
    "chosun.com": "조선일보",
    "donga.com": "동아일보",
    "joongang.co.kr": "중앙일보",
    "hankookilbo.com": "한국일보",
    "khan.co.kr": "경향신문",
    "newsis.com": "뉴시스",
    "news1.kr": "뉴스1",
    "fnnews.com": "파이낸셜뉴스",
    "mt.co.kr": "머니투데이",
    "edaily.co.kr": "이데일리",
    "heraldcorp.com": "헤럴드경제",
    "asiae.co.kr": "아시아경제",
    "einfomax.co.kr": "연합인포맥스",
    "newspim.com": "뉴스핌",
    "etnews.com": "전자신문",
    "dt.co.kr": "디지털타임스",
    "ajunews.com": "아주경제",
}

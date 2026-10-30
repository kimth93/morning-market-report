from __future__ import annotations

from typing import Any, Callable, Optional

import requests

from app.config import Settings

NAVER_NEWS_URL = "https://openapi.naver.com/v1/search/news.json"
MAX_DISPLAY = 100
TIMEOUT_SECONDS = 10


class NaverAPIError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def fetch_news(
    query: str,
    settings: Settings,
    display: int = MAX_DISPLAY,
    sort: str = "date",
    http_get: Optional[Callable[..., Any]] = None,
) -> list[dict]:
    if not 1 <= display <= MAX_DISPLAY:
        raise ValueError(f"display는 1~{MAX_DISPLAY} 사이여야 합니다: {display}")

    get = http_get or requests.get
    headers = {
        "X-Naver-Client-Id": settings.naver_client_id,
        "X-Naver-Client-Secret": settings.naver_client_secret,
    }
    params = {"query": query, "display": display, "sort": sort}

    try:
        response = get(NAVER_NEWS_URL, headers=headers, params=params, timeout=TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        raise NaverAPIError(f"네이버 API 요청 실패: {exc}") from exc

    if response.status_code != 200:
        raise NaverAPIError(
            f"네이버 API 오류 응답: {response.status_code}",
            status_code=response.status_code,
        )

    return response.json().get("items", [])

from __future__ import annotations

import pytest
import requests

from app.collectors.naver_news import NaverAPIError, fetch_news
from app.config import Settings


class FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self) -> dict:
        return self._payload


@pytest.fixture
def settings() -> Settings:
    return Settings(
        claude_api_key="test-claude-key",
        naver_client_id="test-naver-id",
        naver_client_secret="test-naver-secret",
        database_url="sqlite:///./app.db",
    )


def test_returns_items_and_sends_auth_headers_and_params(settings):
    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse(200, {"items": [{"title": "코스피 상승"}]})

    items = fetch_news("코스피", settings, http_get=fake_get)

    assert items == [{"title": "코스피 상승"}]
    url, kwargs = calls[0]
    assert url == "https://openapi.naver.com/v1/search/news.json"
    assert kwargs["headers"] == {
        "X-Naver-Client-Id": "test-naver-id",
        "X-Naver-Client-Secret": "test-naver-secret",
    }
    assert kwargs["params"] == {"query": "코스피", "display": 100, "sort": "date"}


def test_unauthorized_raises_naver_error_with_status(settings):
    def fake_get(url, **kwargs):
        return FakeResponse(401)

    with pytest.raises(NaverAPIError) as excinfo:
        fetch_news("코스피", settings, http_get=fake_get)

    assert excinfo.value.status_code == 401


def test_rate_limited_raises_naver_error_with_status(settings):
    def fake_get(url, **kwargs):
        return FakeResponse(429)

    with pytest.raises(NaverAPIError) as excinfo:
        fetch_news("코스피", settings, http_get=fake_get)

    assert excinfo.value.status_code == 429


def test_timeout_raises_naver_error_without_status(settings):
    def fake_get(url, **kwargs):
        raise requests.Timeout("timed out")

    with pytest.raises(NaverAPIError) as excinfo:
        fetch_news("코스피", settings, http_get=fake_get)

    assert excinfo.value.status_code is None


def test_display_above_naver_limit_is_rejected(settings):
    def fake_get(url, **kwargs):
        raise AssertionError("should not call the network")

    with pytest.raises(ValueError):
        fetch_news("코스피", settings, display=101, http_get=fake_get)

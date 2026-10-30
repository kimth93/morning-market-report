from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(autouse=True)
def configured_env(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAUDE_API_KEY", "test-claude-key")
    monkeypatch.setenv("NAVER_CLIENT_ID", "test-naver-id")
    monkeypatch.setenv("NAVER_CLIENT_SECRET", "test-naver-secret")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")


def test_health_returns_ok():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_startup_exposes_session_factory():
    with TestClient(app):
        assert app.state.session_factory is not None


def test_cors_allows_local_frontend_origin():
    with TestClient(app) as client:
        response = client.options(
            "/api/news/generate",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            },
        )

    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_rejects_unknown_origin():
    with TestClient(app) as client:
        response = client.options(
            "/api/news/generate",
            headers={
                "Origin": "http://evil.example",
                "Access-Control-Request-Method": "POST",
            },
        )

    assert "access-control-allow-origin" not in response.headers

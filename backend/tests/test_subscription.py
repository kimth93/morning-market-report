from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import EmailSubscriber


@pytest.fixture(autouse=True)
def configured_env(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAUDE_API_KEY", "test-claude-key")
    monkeypatch.setenv("NAVER_CLIENT_ID", "test-naver-id")
    monkeypatch.setenv("NAVER_CLIENT_SECRET", "test-naver-secret")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")


def test_signup_stores_subscriber_and_returns_id():
    with TestClient(app) as client:
        response = client.post(
            "/api/subscription/signup",
            json={"email": "reader@example.com", "name": "김투자"},
        )
        session = app.state.session_factory()
        row = session.query(EmailSubscriber).filter_by(email="reader@example.com").one()
        session.close()

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["subscription_id"] == str(row.id)
    assert row.name == "김투자"


def test_signup_rejects_invalid_email():
    with TestClient(app) as client:
        response = client.post("/api/subscription/signup", json={"email": "not-an-email", "name": "김투자"})

    assert response.status_code == 422


def test_signup_requires_name():
    with TestClient(app) as client:
        response = client.post("/api/subscription/signup", json={"email": "reader@example.com"})

    assert response.status_code == 422

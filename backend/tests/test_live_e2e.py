from __future__ import annotations

import logging
import os
import time

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.reliability import check_report

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(os.environ.get("RUN_LIVE") != "1", reason="RUN_LIVE=1일 때만 실행"),
]

MAX_SECONDS = 5 * 60


def test_full_flow_meets_reliability_checks_and_logs_usage(monkeypatch, tmp_path, caplog):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'e2e.db'}")
    caplog.set_level(logging.INFO)

    started = time.monotonic()
    with TestClient(app) as client:
        response = client.post("/api/news/generate")
    elapsed = time.monotonic() - started

    assert response.status_code == 200
    assert elapsed < MAX_SECONDS
    payload = response.json()
    assert len(payload["news_items"]) == 5

    findings = check_report(payload)
    failures = [f.message for f in findings if f.level == "fail"]
    assert failures == []

    # 비용 추적: 요약 5건과 전망 1건의 토큰 사용량이 로그에 남아야 한다.
    usage_lines = [r.getMessage() for r in caplog.records if "input_tokens=" in r.getMessage()]
    assert len(usage_lines) == 6

    print(f"\n생성 시간: {elapsed:.1f}초")
    for finding in findings:
        print(f"[{finding.level}] {finding.message}")
    for line in usage_lines:
        print(line)

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_DATABASE_URL = "sqlite:///./app.db"
REQUIRED_KEYS = ("CLAUDE_API_KEY", "NAVER_CLIENT_ID", "NAVER_CLIENT_SECRET")
# .env는 실행 위치(cwd)가 아니라 backend/ 디렉터리에서 찾는다.
DEFAULT_DOTENV_PATH = Path(__file__).resolve().parent.parent / ".env"


@dataclass(frozen=True)
class Settings:
    claude_api_key: str
    naver_client_id: str
    naver_client_secret: str
    database_url: str


def get_settings(dotenv_path: str | Path | None = None) -> Settings:
    load_dotenv(dotenv_path or DEFAULT_DOTENV_PATH)

    missing = [key for key in REQUIRED_KEYS if not os.environ.get(key)]
    if missing:
        raise ValueError(f"필수 환경 변수가 없습니다: {', '.join(missing)}")

    return Settings(
        claude_api_key=os.environ["CLAUDE_API_KEY"],
        naver_client_id=os.environ["NAVER_CLIENT_ID"],
        naver_client_secret=os.environ["NAVER_CLIENT_SECRET"],
        database_url=os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL),
    )

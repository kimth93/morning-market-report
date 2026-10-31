from __future__ import annotations

import pytest

from app.config import get_settings

REQUIRED_KEYS = ("CLAUDE_API_KEY", "NAVER_CLIENT_ID", "NAVER_CLIENT_SECRET")


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for key in (*REQUIRED_KEYS, "DATABASE_URL"):
        monkeypatch.delenv(key, raising=False)


def write_env(tmp_path, lines: list[str]) -> str:
    env_file = tmp_path / ".env"
    env_file.write_text("\n".join(lines) + "\n")
    return str(env_file)


def test_loads_required_keys_from_env_file(tmp_path):
    path = write_env(
        tmp_path,
        [
            "CLAUDE_API_KEY=test-claude-key",
            "NAVER_CLIENT_ID=test-naver-id",
            "NAVER_CLIENT_SECRET=test-naver-secret",
            "DATABASE_URL=sqlite:///./other.db",
        ],
    )

    settings = get_settings(dotenv_path=path)

    assert settings.claude_api_key == "test-claude-key"
    assert settings.naver_client_id == "test-naver-id"
    assert settings.naver_client_secret == "test-naver-secret"
    assert settings.database_url == "sqlite:///./other.db"


def test_database_url_defaults_when_unset(tmp_path):
    path = write_env(
        tmp_path,
        [
            "CLAUDE_API_KEY=test-claude-key",
            "NAVER_CLIENT_ID=test-naver-id",
            "NAVER_CLIENT_SECRET=test-naver-secret",
        ],
    )

    settings = get_settings(dotenv_path=path)

    assert settings.database_url == "sqlite:///./app.db"


def test_missing_required_key_raises_value_error(tmp_path):
    path = write_env(
        tmp_path,
        [
            "CLAUDE_API_KEY=test-claude-key",
            "NAVER_CLIENT_ID=test-naver-id",
        ],
    )

    with pytest.raises(ValueError, match="NAVER_CLIENT_SECRET"):
        get_settings(dotenv_path=path)


def test_default_dotenv_is_resolved_from_module_not_cwd(monkeypatch, tmp_path):
    from app import config as config_module

    env_file = tmp_path / "module.env"
    env_file.write_text(
        "CLAUDE_API_KEY=from-module-file\n"
        "NAVER_CLIENT_ID=from-module-file\n"
        "NAVER_CLIENT_SECRET=from-module-file\n"
    )
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.setattr(config_module, "DEFAULT_DOTENV_PATH", env_file)
    monkeypatch.chdir(elsewhere)

    settings = get_settings()

    assert settings.naver_client_id == "from-module-file"


def test_default_dotenv_points_at_backend_env():
    from pathlib import Path

    from app import config as config_module

    backend_dir = Path(__file__).resolve().parent.parent
    assert config_module.DEFAULT_DOTENV_PATH == backend_dir / ".env"

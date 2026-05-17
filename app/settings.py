from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database_url: str
    redis_url: str
    jwt_secret: str
    access_token_ttl_seconds: int
    refresh_ttl_seconds: int
    github_client_id: str | None
    github_client_secret: str | None
    base_url: str
    llm_model_path: str | None


def get_settings() -> Settings:
    project_root = Path(__file__).resolve().parents[1]

    env_path = project_root / ".env"
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path, override=False)

    raw_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/chatapp")
    if "+asyncpg" not in raw_url:
        database_url = raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    else:
        database_url = raw_url

    model_path = os.getenv("MODEL_PATH") or None
    if model_path is None:
        default_model = project_root / "model.gguf"
        if default_model.exists():
            model_path = str(default_model)

    return Settings(
        database_url=database_url,
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        jwt_secret=(os.getenv("SECRET_KEY") or "").strip(),
        access_token_ttl_seconds=int(os.getenv("ACCESS_TTL_SECONDS", "1800")),
        refresh_ttl_seconds=int(os.getenv("REFRESH_TTL_SECONDS", str(30 * 24 * 60 * 60))),
        github_client_id=os.getenv("GITHUB_CLIENT_ID") or None,
        github_client_secret=os.getenv("GITHUB_CLIENT_SECRET") or None,
        base_url=os.getenv("BASE_URL", "http://127.0.0.1:8000"),
        llm_model_path=model_path,
    )

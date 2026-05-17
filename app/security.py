from __future__ import annotations

import secrets
import time
from dataclasses import dataclass
from typing import Any

import bcrypt
from jose import JWTError, jwt

from .settings import get_settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except Exception:
        return False


@dataclass(frozen=True)
class Tokens:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


def create_access_token(subject: str, extra: dict[str, Any] | None = None) -> str:
    s = get_settings()
    if not s.jwt_secret:
        raise RuntimeError("SECRET_KEY is required")
    now = int(time.time())
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": now + s.access_token_ttl_seconds,
        "type": "access",
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, s.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any]:
    s = get_settings()
    if not s.jwt_secret:
        raise RuntimeError("SECRET_KEY is required")
    payload = jwt.decode(token, s.jwt_secret, algorithms=["HS256"])
    if payload.get("type") != "access":
        raise JWTError("invalid_token_type")
    return payload


def new_refresh_token() -> str:
    return secrets.token_urlsafe(32)

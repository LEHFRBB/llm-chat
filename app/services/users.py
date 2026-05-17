from __future__ import annotations

from typing import Any

from sqlalchemy import select

from ..db import get_session_factory
from ..models.user import User
from ..security import hash_password, verify_password


def _to_dict(user: User) -> dict[str, Any]:
    return {
        "_id": str(user.id),
        "login": user.login,
        "password_hash": user.password or "",
        "github_id": user.github_id,
    }


async def create_user(login: str, password: str) -> dict[str, Any]:
    async with get_session_factory()() as session:
        user = User(login=login, password=hash_password(password))
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return _to_dict(user)


async def get_user_by_login(login: str) -> dict[str, Any] | None:
    async with get_session_factory()() as session:
        result = await session.execute(select(User).where(User.login == login))
        user = result.scalar_one_or_none()
        return _to_dict(user) if user else None


async def get_user_by_id(user_id: str) -> dict[str, Any] | None:
    async with get_session_factory()() as session:
        try:
            uid = int(user_id)
        except (ValueError, TypeError):
            return None
        result = await session.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()
        return _to_dict(user) if user else None


def verify_user_password(user: dict[str, Any], password: str) -> bool:
    return verify_password(password, str(user.get("password_hash", "")))


async def upsert_github_user(github_id: int, login_hint: str) -> dict[str, Any]:
    async with get_session_factory()() as session:
        result = await session.execute(select(User).where(User.github_id == str(github_id)))
        user = result.scalar_one_or_none()
        if user:
            return _to_dict(user)

        base = login_hint[:48] or "github"
        candidate = base
        i = 0
        while True:
            taken = await session.execute(select(User).where(User.login == candidate))
            if not taken.scalar_one_or_none():
                break
            i += 1
            candidate = f"{base}{i}"

        user = User(login=candidate, github_id=str(github_id), password=None)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return _to_dict(user)

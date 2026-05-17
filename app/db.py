from __future__ import annotations

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from .settings import get_settings

Base = declarative_base()


@lru_cache(maxsize=1)
def _engine():
    return create_async_engine(get_settings().database_url, echo=False)


@lru_cache(maxsize=1)
def _factory() -> async_sessionmaker:
    return async_sessionmaker(_engine(), class_=AsyncSession, expire_on_commit=False)


def get_session_factory() -> async_sessionmaker:
    return _factory()


async def init_db() -> None:
    pass

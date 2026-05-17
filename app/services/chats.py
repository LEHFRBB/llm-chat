from __future__ import annotations

from typing import Any

from sqlalchemy import delete, select

from ..db import get_session_factory
from ..models.chat import Chat
from ..models.message import Message


def _chat_to_dict(chat: Chat) -> dict[str, Any]:
    created_at = chat.created_at
    created_at_str = created_at.isoformat() if created_at and hasattr(created_at, "isoformat") else str(created_at or "")
    return {
        "_id": str(chat.id),
        "id": str(chat.id),
        "user_id": str(chat.user_id),
        "title": chat.title,
        "created_at": created_at_str,
    }


def _msg_to_dict(msg: Message) -> dict[str, Any]:
    created_at = msg.created_at
    created_at_str = created_at.isoformat() if created_at and hasattr(created_at, "isoformat") else str(created_at or "")
    return {
        "_id": str(msg.id),
        "id": str(msg.id),
        "chat_id": str(msg.chat_id),
        "role": msg.role,
        "content": msg.content,
        "created_at": created_at_str,
    }


async def create_chat(user_id: str, title: str) -> dict[str, Any]:
    async with get_session_factory()() as session:
        chat = Chat(user_id=int(user_id), title=title)
        session.add(chat)
        await session.commit()
        await session.refresh(chat)
        return _chat_to_dict(chat)


async def list_chats(user_id: str) -> list[dict[str, Any]]:
    async with get_session_factory()() as session:
        result = await session.execute(
            select(Chat).where(Chat.user_id == int(user_id)).order_by(Chat.created_at.desc())
        )
        return [_chat_to_dict(c) for c in result.scalars().all()]


async def get_chat(user_id: str, chat_id: str) -> dict[str, Any] | None:
    async with get_session_factory()() as session:
        result = await session.execute(
            select(Chat).where(Chat.id == int(chat_id), Chat.user_id == int(user_id))
        )
        chat = result.scalar_one_or_none()
        return _chat_to_dict(chat) if chat else None


async def list_messages(user_id: str, chat_id: str) -> list[dict[str, Any]]:
    async with get_session_factory()() as session:
        result = await session.execute(
            select(Message).where(Message.chat_id == int(chat_id)).order_by(Message.id)
        )
        return [_msg_to_dict(m) for m in result.scalars().all()]


async def add_message(chat_id: str, user_id: str, role: str, content: str) -> dict[str, Any]:
    async with get_session_factory()() as session:
        msg = Message(chat_id=int(chat_id), role=role, content=content)
        session.add(msg)
        await session.commit()
        await session.refresh(msg)
        return _msg_to_dict(msg)


async def delete_chat(user_id: str, chat_id: str) -> bool:
    async with get_session_factory()() as session:
        result = await session.execute(
            select(Chat).where(Chat.id == int(chat_id), Chat.user_id == int(user_id))
        )
        chat = result.scalar_one_or_none()
        if not chat:
            return False
        await session.execute(delete(Message).where(Message.chat_id == int(chat_id)))
        await session.delete(chat)
        await session.commit()
        return True

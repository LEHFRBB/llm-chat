from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from .api.auth import oauth_router, router as auth_router
from .api.chats import router as chats_router
from .api.llm import router as llm_router
from .redis_client import get_redis
from .security import create_access_token, decode_access_token
from .web.pages import router as pages_router

app = FastAPI(title="LLM Chat")

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

app.include_router(pages_router)
app.include_router(auth_router)
app.include_router(oauth_router)
app.include_router(chats_router)
app.include_router(llm_router)


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    request.state.user_id = None
    new_access_token: Optional[str] = None

    access_token = request.cookies.get("access_token")
    if access_token:
        try:
            payload = decode_access_token(access_token)
            request.state.user_id = str(payload.get("sub") or "")
        except Exception:
            pass

    if not request.state.user_id:
        refresh_token = request.cookies.get("refresh_token")
        if refresh_token:
            try:
                r = get_redis()
                user_id = await r.get(f"refresh:{refresh_token}")
                if user_id:
                    request.state.user_id = str(user_id)
                    new_access_token = create_access_token(str(user_id))
            except Exception:
                pass

    response = await call_next(request)
    if new_access_token:
        response.set_cookie("access_token", new_access_token, httponly=True, max_age=1800)
    return response

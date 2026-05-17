from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from ..schemas import ChatCreateIn, SendMessageIn
from ..security import create_access_token
from ..services import auth_usecases, chats_usecases
from ..services.auth import issue_tokens, new_oauth_state, store_oauth_state
from ..services.chats import delete_chat, list_chats
from ..services.oauth_github import build_authorize_url
from ..services.users import create_user, get_user_by_id, get_user_by_login, verify_user_password
from ..settings import get_settings

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
templates.env.filters["datefmt"] = lambda s: str(s)[:16].replace("T", " ") if s else ""

router = APIRouter(tags=["ui"])


def _github_enabled() -> bool:
    return bool(get_settings().github_client_id)


def _set_auth_cookies(response: Any, access_token: str, refresh_token: str) -> None:
    s = get_settings()
    response.set_cookie("access_token", access_token, httponly=True, max_age=s.access_token_ttl_seconds)
    response.set_cookie("refresh_token", refresh_token, httponly=True, max_age=s.refresh_ttl_seconds)


def _clear_auth_cookies(response: Any) -> None:
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")


# ── Home (chats list) ──────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> Any:
    user_id = request.state.user_id
    if not user_id:
        return RedirectResponse("/login", 303)
    user = await get_user_by_id(user_id)
    chats = await list_chats(user_id)
    return templates.TemplateResponse(request, "chats.html", {"user": user, "chats": chats})


# ── Register ───────────────────────────────────────────────────────────────────

@router.get("/register", response_class=HTMLResponse)
async def register_get(request: Request) -> Any:
    if request.state.user_id:
        return RedirectResponse("/", 303)
    return templates.TemplateResponse(
        request, "register.html", {"github_enabled": _github_enabled()}
    )


@router.post("/register", response_class=HTMLResponse)
async def register_post(
    request: Request,
    login: str = Form(...),
    password: str = Form(...),
    password2: str = Form(...),
) -> Any:
    ctx: dict[str, Any] = {"github_enabled": _github_enabled(), "login_val": login}
    if password != password2:
        return templates.TemplateResponse(request, "register.html", {**ctx, "error": "Passwords do not match."})
    if len(password) < 6:
        return templates.TemplateResponse(request, "register.html", {**ctx, "error": "Password must be at least 6 characters."})
    existing = await get_user_by_login(login.strip())
    if existing:
        return templates.TemplateResponse(request, "register.html", {**ctx, "error": "Username is already taken."})
    u = await create_user(login.strip(), password)
    tokens = await issue_tokens(u["_id"], u["login"])
    response = RedirectResponse("/", 303)
    _set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
    return response


# ── Login ──────────────────────────────────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse)
async def login_get(request: Request) -> Any:
    if request.state.user_id:
        return RedirectResponse("/", 303)
    error = request.query_params.get("error") or None
    return templates.TemplateResponse(
        request, "login.html", {"github_enabled": _github_enabled(), "error": error}
    )


@router.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    login: str = Form(...),
    password: str = Form(...),
) -> Any:
    u = await get_user_by_login(login.strip())
    if not u or not verify_user_password(u, password):
        return templates.TemplateResponse(
            request, "login.html",
            {"error": "Invalid credentials.", "github_enabled": _github_enabled()}
        )
    tokens = await issue_tokens(u["_id"], u["login"])
    response = RedirectResponse("/", 303)
    _set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
    return response


# ── Logout ─────────────────────────────────────────────────────────────────────

@router.get("/logout")
async def logout() -> RedirectResponse:
    response = RedirectResponse("/login", 303)
    _clear_auth_cookies(response)
    return response


# ── GitHub OAuth start ─────────────────────────────────────────────────────────

@router.get("/auth/github")
async def github_start(request: Request) -> Any:
    try:
        state = new_oauth_state()
        await store_oauth_state(state)
        url = build_authorize_url(state)  # uses BASE_URL from settings
        return RedirectResponse(url, 302)
    except RuntimeError as exc:
        msg = str(exc)
        if "GITHUB_CLIENT_ID" in msg:
            error = "GitHub OAuth is not configured (GITHUB_CLIENT_ID missing)."
        else:
            error = f"GitHub OAuth error: {msg}"
    except Exception as exc:
        error = f"GitHub OAuth error: {exc}"
    return templates.TemplateResponse(
        request, "login.html", {"error": error, "github_enabled": _github_enabled()}
    )


# ── Chat ───────────────────────────────────────────────────────────────────────

@router.get("/chat/{chat_id}", response_class=HTMLResponse)
async def chat_page(request: Request, chat_id: str) -> Any:
    user_id = request.state.user_id
    if not user_id:
        return RedirectResponse("/login", 303)
    user = await get_user_by_id(user_id)
    result = await chats_usecases.get_chat(chat_id, user_id)
    if result is None:
        return RedirectResponse("/", 303)
    return templates.TemplateResponse(
        request, "chat.html",
        {"user": user, "chat": result, "messages": result.messages}
    )


@router.post("/chat/{chat_id}/send")
async def send_message(
    request: Request,
    chat_id: str,
    content: str = Form(...),
) -> RedirectResponse:
    user_id = request.state.user_id
    if not user_id:
        return RedirectResponse("/login", 303)
    content = content.strip()
    if content:
        await chats_usecases.send_message(chat_id, SendMessageIn(content=content), user_id)
    return RedirectResponse(f"/chat/{chat_id}", 303)


@router.post("/create_chat")
async def create_chat(
    request: Request,
    title: str = Form(...),
) -> RedirectResponse:
    user_id = request.state.user_id
    if not user_id:
        return RedirectResponse("/login", 303)
    new_chat = await chats_usecases.create_chat(ChatCreateIn(title=title.strip() or "New Chat"), user_id)
    return RedirectResponse(f"/chat/{new_chat.id}", 303)


@router.post("/chat/{chat_id}/delete")
async def delete_chat_route(
    request: Request,
    chat_id: str,
) -> RedirectResponse:
    user_id = request.state.user_id
    if not user_id:
        return RedirectResponse("/login", 303)
    await delete_chat(user_id, chat_id)
    return RedirectResponse("/", 303)

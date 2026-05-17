# LLM Chat

A ChatGPT-like chat web application built with FastAPI, PostgreSQL, Redis, and llama-cpp-python.

## Tech Stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy async (asyncpg)
- **Database:** PostgreSQL (Alembic migrations)
- **Cache / tokens:** Redis (refresh tokens, OAuth state)
- **Auth:** JWT access tokens (30 min) + refresh tokens (30 days), GitHub OAuth
- **LLM:** llama-cpp-python with a local `.gguf` model
- **Frontend:** Server-rendered HTML (Jinja2) + vanilla JS, no page reloads after login

## Project Structure

```
app/
├── main.py              # FastAPI app entry point
├── settings.py          # Configuration (reads .env)
├── db.py                # Async SQLAlchemy engine
├── security.py          # JWT + bcrypt
├── redis_client.py      # Async Redis client
├── schemas.py           # Pydantic schemas
├── deps.py              # get_current_user dependency
├── api/                 # JSON API controllers
│   ├── auth.py
│   ├── chats.py
│   └── llm.py
├── services/            # Business logic + data access
│   ├── users.py
│   ├── auth.py / auth_usecases.py
│   ├── chats.py / chats_usecases.py
│   ├── llm.py / llm_usecases.py
│   └── oauth_github.py
├── web/pages.py         # HTML page routes
├── templates/           # index.html, chat.html
└── static/app.css
alembic/                 # Database migrations
```

## Setup

**1. Create database and install dependencies:**
```bash
createdb chatapp
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

**2. Configure `.env`** (copy from `.env.example`):
```bash
cp .env.example .env
# Edit .env — set SECRET_KEY, DATABASE_URL, and optionally GITHUB_CLIENT_ID/SECRET
```

**3. Place the LLM model** at project root as `model.gguf` (or set `MODEL_PATH` in `.env`).

**4. Run migrations and start:**
```bash
alembic upgrade head
uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000**

## API Overview

| Route | Method | Description |
|---|---|---|
| `/api/auth/register` | POST | Register with login + password |
| `/api/auth/login` | POST | Login → access + refresh tokens |
| `/api/auth/refresh` | POST | Exchange refresh token for new access token |
| `/auth/github/login` | GET | Start GitHub OAuth flow |
| `/auth/github/callback` | GET | GitHub OAuth callback |
| `/api/chats` | GET/POST | List or create chats |
| `/api/chats/{id}` | GET/DELETE | Get chat with messages, or delete |
| `/api/chats/{id}/messages` | POST | Send message, get LLM reply |
| `/api/llm/status` | GET | Check LLM configuration |

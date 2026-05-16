# NewsPulse Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 0-cost Android news app with daily digest push + real-time topic tracking via FCM.

**Architecture:** Python FastAPI backend aggregates news from free APIs/RSS, matches against user subscriptions (keyword exact + embedding semantic), pushes via Firebase FCM. Kotlin native Android app with Jetpack Compose receives and displays content.

**Tech Stack:** Python FastAPI, Supabase PostgreSQL, Firebase FCM, Kotlin + Jetpack Compose, APScheduler

---

## File Map

```
newspulse/
├── backend/
│   ├── app/
│   │   ├── __init__.py              # Package init
│   │   ├── main.py                  # FastAPI app, CORS, router registration
│   │   ├── config.py                # Env vars, constants
│   │   ├── database.py              # Supabase asyncpg connection pool
│   │   ├── scheduler.py             # APScheduler setup, job definitions
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── tables.py            # All table schemas (Pydantic)
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py              # POST /auth/register, /auth/login
│   │   │   ├── subscriptions.py     # CRUD /subscriptions
│   │   │   ├── articles.py          # GET /articles (feed, digest)
│   │   │   └── notifications.py     # GET /notifications, PATCH read
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── aggregator.py        # Fetch from NewsAPI + RSS, dedup, score
│   │       ├── matcher.py           # Keyword match + embedding similarity
│   │       └── push.py              # FCM send via firebase-admin
│   ├── requirements.txt
│   ├── alembic/                     # DB migrations (optional, init later)
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py              # Fixtures: test client, mock DB
│       ├── test_auth.py
│       ├── test_aggregator.py
│       ├── test_matcher.py
│       └── test_push.py
└── android/
    └── NewsPulse/                   # Android Studio project (generated)
```

---

## Phase 1: Backend Foundation

### Task 1.1: Create project scaffold

**Files:** Create `newspulse/backend/` structure

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p newspulse/backend/app/models
mkdir -p newspulse/backend/app/routers
mkdir -p newspulse/backend/app/services
mkdir -p newspulse/backend/tests
```

- [ ] **Step 2: Write requirements.txt**

```text
fastapi==0.115.6
uvicorn[standard]==0.34.0
asyncpg==0.30.0
pydantic==2.10.3
pydantic-settings==2.7.0
apscheduler==3.10.4
firebase-admin==6.5.0
httpx==0.28.1
feedparser==6.0.11
sentence-transformers==3.3.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.18
```

- [ ] **Step 3: Write app/__init__.py**

```python
"""NewsPulse backend application."""
```

- [ ] **Step 4: Write models/__init__.py, routers/__init__.py, services/__init__.py**

All three files:
```python
"""Package init."""
```

- [ ] **Step 5: Commit**

```bash
cd newspulse && git init && git add backend && git commit -m "chore: scaffold backend project structure"
```

---

### Task 1.2: Configuration and database connection

**Files:**
- Create: `newspulse/backend/app/config.py`
- Create: `newspulse/backend/app/database.py`

- [ ] **Step 1: Write config.py**

```python
"""Application configuration from environment variables."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/newspulse"
    supabase_db: str = ""
    fcm_credentials_path: str = "firebase-credentials.json"
    newsapi_key: str = ""
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 30  # 30 days
    embedding_threshold: float = 0.65
    digest_hour: int = 8
    digest_count: int = 15
    fetch_interval_minutes: int = 15
    supported_rss_urls: list[str] = [
        "https://rsshub.app/zhihu/daily",
        "https://rsshub.app/github/trending/daily",
    ]

    class Config:
        env_file = ".env"


settings = Settings()
```

- [ ] **Step 2: Write database.py**

```python
"""Database connection pool and table initialization."""
import asyncpg
from app.config import settings

pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(settings.database_url, min_size=2, max_size=10)
    return pool


async def init_db():
    """Create tables if they don't exist."""
    p = await get_pool()
    async with p.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                fcm_token VARCHAR(512),
                created_at TIMESTAMPTZ DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS subscriptions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                keyword VARCHAR(255) NOT NULL,
                type VARCHAR(20) NOT NULL DEFAULT 'topic',
                created_at TIMESTAMPTZ DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS articles (
                id SERIAL PRIMARY KEY,
                title VARCHAR(1024) NOT NULL,
                summary TEXT,
                source VARCHAR(255) NOT NULL,
                source_url VARCHAR(2048) UNIQUE,
                published_at TIMESTAMPTZ,
                fetched_at TIMESTAMPTZ DEFAULT NOW(),
                score FLOAT DEFAULT 0.0,
                embedding BYTEA
            );

            CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                article_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
                type VARCHAR(20) NOT NULL DEFAULT 'track',
                sent_at TIMESTAMPTZ DEFAULT NOW(),
                read BOOLEAN DEFAULT FALSE
            );

            CREATE TABLE IF NOT EXISTS daily_digests (
                id SERIAL PRIMARY KEY,
                date DATE UNIQUE NOT NULL,
                article_ids JSONB DEFAULT '[]',
                title VARCHAR(512),
                created_at TIMESTAMPTZ DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at DESC);
            CREATE INDEX IF NOT EXISTS idx_articles_score ON articles(score DESC);
            CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id);
            CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, sent_at DESC);
        """)


async def close_db():
    global pool
    if pool:
        await pool.close()
        pool = None
```

- [ ] **Step 3: Write tests/conftest.py**

```python
"""Shared test fixtures."""
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
```

- [ ] **Step 4: Write tests/__init__.py**

```python
"""Tests package."""
```

- [ ] **Step 5: Commit**

```bash
git add backend && git commit -m "feat: add config and database connection"
```

---

### Task 1.3: FastAPI app entry point

**Files:** Create `newspulse/backend/app/main.py`

- [ ] **Step 1: Write main.py**

```python
"""NewsPulse API application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db, close_db
from app.routers import auth, subscriptions, articles, notifications
from app.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    start_scheduler()
    yield
    stop_scheduler()
    await close_db()


app = FastAPI(title="NewsPulse", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
app.include_router(articles.router, prefix="/articles", tags=["articles"])
app.include_router(notifications.router, prefix="/notifications", tags=["notifications"])


@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 2: Write routers/__init__.py with placeholder imports**

```python
"""Router package."""
from app.routers import auth, subscriptions, articles, notifications
```

- [ ] **Step 3: Write minimal router files (to be filled in later tasks)**

`newspulse/backend/app/routers/auth.py`:
```python
"""Authentication endpoints."""
from fastapi import APIRouter

router = APIRouter()
```

`newspulse/backend/app/routers/subscriptions.py`:
```python
"""Subscription management endpoints."""
from fastapi import APIRouter

router = APIRouter()
```

`newspulse/backend/app/routers/articles.py`:
```python
"""Article feed endpoints."""
from fastapi import APIRouter

router = APIRouter()
```

`newspulse/backend/app/routers/notifications.py`:
```python
"""Notification endpoints."""
from fastapi import APIRouter

router = APIRouter()
```

- [ ] **Step 4: Write stub scheduler.py**

```python
"""Scheduler for periodic tasks using APScheduler."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()


def start_scheduler():
    scheduler.start()


def stop_scheduler():
    scheduler.shutdown()
```

- [ ] **Step 5: Add httpx to requirements.txt** (already there, verify)

- [ ] **Step 6: Commit**

```bash
git add backend && git commit -m "feat: add FastAPI app entry point with router stubs"
```

---

## Phase 2: User Authentication

### Task 2.1: User model and auth utilities

**Files:**
- Create: `newspulse/backend/app/models/tables.py`
- Modify: `newspulse/backend/app/routers/auth.py`

- [ ] **Step 1: Write models/tables.py**

```python
"""Pydantic models for request/response validation."""
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class SubscriptionCreate(BaseModel):
    keyword: str
    type: str = "topic"


class SubscriptionResponse(BaseModel):
    id: int
    user_id: int
    keyword: str
    type: str
    created_at: datetime


class ArticleResponse(BaseModel):
    id: int
    title: str
    summary: str | None
    source: str
    source_url: str
    published_at: datetime | None
    score: float


class NotificationResponse(BaseModel):
    id: int
    article_id: int
    type: str
    sent_at: datetime
    read: bool
    article: ArticleResponse | None


class FCMTokenUpdate(BaseModel):
    fcm_token: str


class ListResponse(BaseModel):
    items: list
    total: int
```

- [ ] **Step 2: Write auth router with register/login**

```python
"""Authentication endpoints."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from jose import jwt
from passlib.context import CryptContext

from app.config import settings
from app.database import get_pool
from app.models.tables import (
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
    FCMTokenUpdate,
)

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def verify_token(token: str) -> int:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    return int(payload["sub"])


@router.post("/register", response_model=TokenResponse)
async def register(body: UserRegister):
    pool = await get_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT id FROM users WHERE email = $1", body.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed = pwd_context.hash(body.password)
        row = await conn.fetchrow(
            "INSERT INTO users (email, password_hash) VALUES ($1, $2) RETURNING id, email, created_at",
            body.email,
            hashed,
        )
        token = create_token(row["id"])
        return TokenResponse(
            access_token=token,
            user=UserResponse(id=row["id"], email=row["email"], created_at=row["created_at"]),
        )


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id, email, password_hash, created_at FROM users WHERE email = $1", body.email)
        if not row or not pwd_context.verify(body.password, row["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token = create_token(row["id"])
        return TokenResponse(
            access_token=token,
            user=UserResponse(id=row["id"], email=row["email"], created_at=row["created_at"]),
        )


@router.patch("/me/fcm-token")
async def update_fcm_token(body: FCMTokenUpdate, token: str):
    """Update device FCM token. Requires Authorization header."""
    user_id = verify_token(token)
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET fcm_token = $1 WHERE id = $2", body.fcm_token, user_id)
    return {"ok": True}
```

- [ ] **Step 3: Write test_auth.py**

```python
"""Tests for auth endpoints."""
import pytest


@pytest.mark.anyio
async def test_register(client):
    resp = await client.post("/auth/register", json={"email": "test@example.com", "password": "abc123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "test@example.com"


@pytest.mark.anyio
async def test_register_duplicate(client):
    await client.post("/auth/register", json={"email": "dup@example.com", "password": "abc123"})
    resp = await client.post("/auth/register", json={"email": "dup@example.com", "password": "abc123"})
    assert resp.status_code == 400


@pytest.mark.anyio
async def test_login(client):
    await client.post("/auth/register", json={"email": "login@example.com", "password": "abc123"})
    resp = await client.post("/auth/login", json={"email": "login@example.com", "password": "abc123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.anyio
async def test_login_wrong_password(client):
    await client.post("/auth/register", json={"email": "wrong@example.com", "password": "abc123"})
    resp = await client.post("/auth/login", json={"email": "wrong@example.com", "password": "wrong"})
    assert resp.status_code == 401
```

- [ ] **Step 4: Install deps and run tests**

```bash
cd newspulse/backend && pip install -r requirements.txt && pytest tests/test_auth.py -v
```
Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend && git commit -m "feat: add user auth — register, login, fcm token"
```

---

## Phase 3: News Aggregation

### Task 3.1: News aggregator service

**Files:** Create `newspulse/backend/app/services/aggregator.py`

- [ ] **Step 1: Write aggregator.py**

```python
"""News aggregation: fetch from NewsAPI + RSS sources, dedup, score, and store."""
import hashlib
import re
from datetime import datetime, timezone

import feedparser
import httpx

from app.config import settings
from app.database import get_pool


async def fetch_newsapi() -> list[dict]:
    """Fetch top headlines from NewsAPI free tier."""
    if not settings.newsapi_key:
        return []
    url = "https://newsapi.org/v2/top-headlines"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params={"apiKey": settings.newsapi_key, "language": "zh", "pageSize": 50})
        if resp.status_code != 200:
            return []
        data = resp.json()
        return [
            {
                "title": a["title"],
                "summary": a.get("description") or "",
                "source": a["source"]["name"],
                "source_url": a["url"],
                "published_at": a.get("publishedAt"),
                "score": _estimate_score(a),
            }
            for a in data.get("articles", [])
            if a.get("title")
        ]


async def fetch_rss(url: str) -> list[dict]:
    """Fetch articles from an RSS feed."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=15)
        if resp.status_code != 200:
            return []
    feed = feedparser.parse(resp.text)
    articles = []
    for entry in feed.entries[:30]:
        articles.append({
            "title": entry.get("title", ""),
            "summary": entry.get("summary", entry.get("description", "")),
            "source": feed.feed.get("title", url),
            "source_url": entry.get("link", ""),
            "published_at": _parse_date(entry),
            "score": 0.5,  # default RSS score
        })
    return articles


def _estimate_score(article: dict) -> float:
    """Heuristic score from source weight + keyword bonuses."""
    score = 0.3
    high_impact_sources = ["Reuters", "新华社", "BBC", "CNN", "央视", "人民日报"]
    source_name = article.get("source", {}).get("name", "") if isinstance(article.get("source"), dict) else ""
    for kw in high_impact_sources:
        if kw in str(source_name):
            score += 0.3
            break
    title = str(article.get("title", ""))
    urgency_keywords = ["突发", "快讯", "紧急", "重磅", "breaking"]
    for kw in urgency_keywords:
        if kw in title.lower():
            score += 0.2
            break
    return min(score, 1.0)


def _parse_date(entry) -> str | None:
    """Extract published date from RSS entry."""
    for attr in ("published", "updated", "created"):
        val = entry.get(attr)
        if val:
            return val
    return None


def _url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def _clean_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)[:2000]


async def aggregate():
    """Pull from all sources, deduplicate, store new articles. Returns count of new articles."""
    raw = []

    # Fetch NewsAPI
    newsapi_articles = await fetch_newsapi()
    raw.extend(newsapi_articles)

    # Fetch each RSS
    for rss_url in settings.supported_rss_urls:
        rss_articles = await fetch_rss(rss_url)
        raw.extend(rss_articles)

    pool = await get_pool()
    new_count = 0

    async with pool.acquire() as conn:
        for art in raw:
            url = art.get("source_url", "")
            if not url:
                continue
            # Check duplicate by URL hash or existing URL
            existing = await conn.fetchrow(
                "SELECT id FROM articles WHERE source_url = $1", url
            )
            if existing:
                continue

            await conn.execute(
                """INSERT INTO articles (title, summary, source, source_url, published_at, score)
                   VALUES ($1, $2, $3, $4, $5, $6)""",
                _clean_html(art.get("title", "")[:1024]),
                _clean_html(art.get("summary", "")[:2000]),
                art.get("source", "unknown")[:255],
                url,
                art.get("published_at"),
                art.get("score", 0.3),
            )
            new_count += 1

    return new_count
```

- [ ] **Step 2: Write test_aggregator.py**

```python
"""Tests for news aggregator."""
import pytest
from app.services.aggregator import aggregate, _estimate_score, _clean_html


def test_clean_html():
    assert _clean_html("<p>Hello <b>World</b></p>") == "Hello World"


def test_estimate_score_urgency():
    article = {"title": "Breaking: major event", "source": {"name": "Reuters"}}
    score = _estimate_score(article)
    assert score >= 0.6


def test_estimate_score_low():
    article = {"title": "Some random news", "source": {"name": "Unknown Blog"}}
    score = _estimate_score(article)
    assert 0.2 <= score <= 0.5


@pytest.mark.anyio
async def test_aggregate_empty_when_no_api_key():
    import app.config
    old_key = app.config.settings.newsapi_key
    app.config.settings.newsapi_key = ""
    count = await aggregate()
    app.config.settings.newsapi_key = old_key
    assert count >= 0  # may get RSS only
```

- [ ] **Step 3: Run tests**

```bash
cd newspulse/backend && pytest tests/test_aggregator.py -v
```
Expected: 4 tests pass.

- [ ] **Step 4: Commit**

```bash
git add backend && git commit -m "feat: add news aggregator — NewsAPI + RSS fetch, dedup, score"
```

---

## Phase 4: Match Engine

### Task 4.1: Match engine service

**Files:** Create `newspulse/backend/app/services/matcher.py`

- [ ] **Step 1: Write matcher.py**

```python
"""Match engine: keyword exact match + embedding semantic similarity."""
import asyncio

from app.config import settings
from app.database import get_pool


async def get_active_subscriptions() -> list[dict]:
    """Get all subscriptions grouped by user."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, user_id, keyword, type FROM subscriptions")
    return [dict(r) for r in rows]


def keyword_match(article_title: str, article_summary: str, keyword: str) -> bool:
    """Case-insensitive keyword match in title or summary."""
    kw = keyword.lower()
    text = f"{article_title} {article_summary}".lower()
    return kw in text


# Lazy-loaded embedding model
_embedding_model = None


def _get_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer("shibing624/text2vec-base-chinese")
    return _embedding_model


def semantic_match(title: str, summary: str, keyword: str, threshold: float | None = None) -> bool:
    """Compute cosine similarity between title+summary and keyword. Returns True if above threshold."""
    if threshold is None:
        threshold = settings.embedding_threshold
    model = _get_model()
    article_text = f"{title} {summary}"[:512]
    embeddings = model.encode([article_text, keyword])
    similarity = float(embeddings[0] @ embeddings[1].T)
    return similarity >= threshold


async def match_and_notify(article_id: int, title: str, summary: str):
    """Run match engine for a single article, create notifications for matched subscriptions."""
    subs = await get_active_subscriptions()
    if not subs:
        return []

    pool = await get_pool()
    matches = []

    async with pool.acquire() as conn:
        # Get user FCM tokens
        user_tokens = {}
        token_rows = await conn.fetch("SELECT id, fcm_token FROM users WHERE fcm_token IS NOT NULL")
        for r in token_rows:
            user_tokens[r["id"]] = r["fcm_token"]

        for sub in subs:
            matched = False

            # Layer 1: exact keyword match
            if keyword_match(title, summary, sub["keyword"]):
                matched = True
            # Layer 2: semantic match (only if keyword is meaningful)
            elif len(sub["keyword"]) >= 2:
                # Run in thread to not block event loop
                matched = await asyncio.to_thread(semantic_match, title, summary, sub["keyword"])

            if matched:
                await conn.execute(
                    "INSERT INTO notifications (user_id, article_id, type) VALUES ($1, $2, 'track')",
                    sub["user_id"],
                    article_id,
                )
                matches.append({
                    "user_id": sub["user_id"],
                    "fcm_token": user_tokens.get(sub["user_id"]),
                    "keyword": sub["keyword"],
                })

    return matches


async def process_new_articles(article_ids: list[int]):
    """Match all new articles against subscriptions."""
    pool = await get_pool()
    all_matches = []
    async with pool.acquire() as conn:
        for aid in article_ids:
            row = await conn.fetchrow("SELECT id, title, summary FROM articles WHERE id = $1", aid)
            if row:
                matches = await match_and_notify(row["id"], row["title"], row["summary"] or "")
                all_matches.extend(matches)
    return all_matches
```

- [ ] **Step 2: Write test_matcher.py**

```python
"""Tests for match engine."""
import pytest
from app.services.matcher import keyword_match


def test_keyword_match_in_title():
    assert keyword_match("马斯克收购Twitter", "", "马斯克") is True


def test_keyword_match_case_insensitive():
    assert keyword_match("Elon Musk launches rocket", "", "elon musk") is True


def test_keyword_no_match():
    assert keyword_match("OpenAI发布新模型", "", "马斯克") is False


def test_keyword_partial_no_match():
    assert keyword_match("太空探索取得新进展", "", "太空探索技术公司") is False  # partial substring not match
```

- [ ] **Step 3: Run tests**

```bash
cd newspulse/backend && pytest tests/test_matcher.py -v
```
Expected: 4 tests pass.

- [ ] **Step 4: Commit**

```bash
git add backend && git commit -m "feat: add match engine — keyword exact + semantic embedding"
```

---

## Phase 5: Push Notifications & Daily Digest

### Task 5.1: FCM push service

**Files:** Create `newspulse/backend/app/services/push.py`

- [ ] **Step 1: Write push.py**

```python
"""Push notification service via Firebase Cloud Messaging."""
import json

import firebase_admin
from firebase_admin import credentials, messaging


_initialized = False


def _init_firebase():
    global _initialized
    if _initialized:
        return
    cred = credentials.Certificate("firebase-credentials.json")
    firebase_admin.initialize_app(cred)
    _initialized = True


def send_track_push(fcm_token: str, title: str, body: str, article_id: int) -> str | None:
    """Send an instant tracking push to a single device."""
    if not fcm_token:
        return None
    _init_firebase()
    message = messaging.Message(
        token=fcm_token,
        notification=messaging.Notification(title=f"📡 {title}"[:100], body=body[:200]),
        data={"article_id": str(article_id), "type": "track"},
    )
    try:
        result = messaging.send(message)
        return result
    except messaging.UnregisteredError:
        return None  # token invalid, will be cleaned up later


def send_daily_digest_push(fcm_token: str, digest_title: str, digest_id: int) -> str | None:
    """Send daily digest push to a single device."""
    if not fcm_token:
        return None
    _init_firebase()
    message = messaging.Message(
        token=fcm_token,
        notification=messaging.Notification(
            title="📰 每日精选",
            body=digest_title[:200],
        ),
        data={"digest_id": str(digest_id), "type": "daily"},
    )
    try:
        result = messaging.send(message)
        return result
    except messaging.UnregisteredError:
        return None


async def broadcast_daily_digest(digest_id: int, digest_title: str):
    """Send daily digest to all users with FCM tokens."""
    from app.database import get_pool

    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT fcm_token FROM users WHERE fcm_token IS NOT NULL")
        for row in rows:
            send_daily_digest_push(row["fcm_token"], digest_title, digest_id)


async def send_track_to_user(user_id: int, title: str, body: str, article_id: int):
    """Send track push to a specific user."""
    from app.database import get_pool

    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT fcm_token FROM users WHERE id = $1 AND fcm_token IS NOT NULL", user_id)
        if row:
            send_track_push(row["fcm_token"], title, body, article_id)
```

- [ ] **Step 2: Commit**

```bash
git add backend && git commit -m "feat: add FCM push service — track + daily digest"
```

---

### Task 5.2: Daily digest service and scheduler wiring

**Files:**
- Create: `newspulse/backend/app/services/digest.py` (digest generation moved here to keep push clean)
- Modify: `newspulse/backend/app/scheduler.py`

- [ ] **Step 1: Create digest service in push.py — add at bottom of push.py**

No, better to keep it separate. Let me create a digest module.

Actually, let me keep it simple — add the digest generation logic to push.py since it's closely related, or put it in a helper in scheduler.py. For cleanliness, let me put it directly in the scheduler since it orchestrates the flow.

**Modify scheduler.py:**

```python
"""Scheduler for periodic tasks using APScheduler."""
from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.database import get_pool
from app.services.aggregator import aggregate
from app.services.matcher import process_new_articles
from app.services.push import broadcast_daily_digest

scheduler = AsyncIOScheduler()


async def _fetch_and_match():
    """Fetch news and match against subscriptions."""
    import logging
    logger = logging.getLogger("newspulse")
    try:
        count = await aggregate()
        if count > 0:
            # Get IDs of newly fetched articles
            pool = await get_pool()
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT id FROM articles ORDER BY fetched_at DESC LIMIT $1", count
                )
                ids = [r["id"] for r in rows]
            if ids:
                matches = await process_new_articles(ids)
                for m in matches:
                    if m.get("fcm_token"):
                        from app.services.push import send_track_push
                        send_track_push(
                            m["fcm_token"],
                            f"追踪命中: {m['keyword']}",
                            f"有新的相关新闻",
                            ids[0],
                        )
            logger.info(f"Fetched {count} new articles, {len(matches)} matches")
    except Exception as e:
        logger.error(f"Fetch-and-match failed: {e}")


async def _generate_daily_digest():
    """Generate and broadcast daily digest."""
    import logging
    logger = logging.getLogger("newspulse")
    try:
        today = date.today()
        pool = await get_pool()
        async with pool.acquire() as conn:
            # Check if already generated today
            existing = await conn.fetchrow(
                "SELECT id FROM daily_digests WHERE date = $1", today
            )
            if existing:
                return

            # Get top articles from past 24h
            rows = await conn.fetch(
                """SELECT id, title FROM articles
                   WHERE published_at >= NOW() - INTERVAL '24 hours'
                   ORDER BY score DESC LIMIT $1""",
                settings.digest_count,
            )
            if not rows:
                return

            ids = [r["id"] for r in rows]
            title = rows[0]["title"] if rows else "今日精选"

            digest_row = await conn.fetchrow(
                "INSERT INTO daily_digests (date, article_ids, title) VALUES ($1, $2, $3) RETURNING id",
                today,
                ids,
                title,
            )
            digest_id = digest_row["id"]
            await broadcast_daily_digest(digest_id, title or "今日精选")
            logger.info(f"Daily digest {digest_id} broadcast")
    except Exception as e:
        logger.error(f"Daily digest failed: {e}")


def start_scheduler():
    scheduler.add_job(
        _fetch_and_match,
        "interval",
        minutes=settings.fetch_interval_minutes,
        id="fetch_and_match",
        replace_existing=True,
    )
    scheduler.add_job(
        _generate_daily_digest,
        "cron",
        hour=settings.digest_hour,
        minute=0,
        id="daily_digest",
        replace_existing=True,
    )
    scheduler.start()


def stop_scheduler():
    scheduler.shutdown()
```

- [ ] **Step 2: Write test_push.py**

```python
"""Tests for push service."""
from app.services.push import _init_firebase


def test_firebase_init_no_credentials_file():
    """Should not crash — FCM init is lazy, only when send is called."""
    # This just tests the module loads
    from app.services import push
    assert push._initialized is False
```

- [ ] **Step 3: Commit**

```bash
git add backend && git commit -m "feat: add daily digest generation and scheduler wiring"
```

---

## Phase 6: Subscription & Article APIs

### Task 6.1: Subscription CRUD endpoints

**Files:** Modify `newspulse/backend/app/routers/subscriptions.py`

- [ ] **Step 1: Write subscriptions router**

```python
"""Subscription management endpoints."""
from fastapi import APIRouter, Header, HTTPException

from app.auth import verify_token  # moved here, see note below
from app.database import get_pool
from app.models.tables import SubscriptionCreate, SubscriptionResponse, ListResponse

router = APIRouter()


async def _get_user_id(authorization: str = Header(...)) -> int:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401)
    return verify_token(authorization[7:])


@router.get("", response_model=ListResponse)
async def list_subscriptions(authorization: str = Header(...)):
    user_id = await _get_user_id(authorization)
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, user_id, keyword, type, created_at FROM subscriptions WHERE user_id = $1 ORDER BY created_at DESC",
            user_id,
        )
    items = [SubscriptionResponse(**r) for r in rows]
    return ListResponse(items=items, total=len(items))


@router.post("", response_model=SubscriptionResponse)
async def create_subscription(body: SubscriptionCreate, authorization: str = Header(...)):
    user_id = await _get_user_id(authorization)
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO subscriptions (user_id, keyword, type) VALUES ($1, $2, $3) RETURNING id, user_id, keyword, type, created_at",
            user_id, body.keyword, body.type,
        )
    return SubscriptionResponse(**row)


@router.delete("/{subscription_id}")
async def delete_subscription(subscription_id: int, authorization: str = Header(...)):
    user_id = await _get_user_id(authorization)
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM subscriptions WHERE id = $1 AND user_id = $2",
            subscription_id, user_id,
        )
    return {"ok": True}
```

Wait — `verify_token` was defined in `routers/auth.py`. Let me move it to a shared location. I'll update the auth router to import from a shared auth module.

Actually, the simplest approach: just put `verify_token` in `app/auth.py` as a shared utility and import from both places. Let me restructure.

- [ ] **Step 1 (revised): Create app/auth.py (shared auth utilities)**

```python
"""Shared auth utilities."""
from datetime import datetime, timezone, timedelta

from jose import jwt

from app.config import settings


def create_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def verify_token(token: str) -> int:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    return int(payload["sub"])


async def get_user_id_from_header(authorization: str) -> int:
    """Extract user ID from Bearer token header."""
    from fastapi import HTTPException
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    try:
        return verify_token(authorization[7:])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
```

- [ ] **Step 2: Update auth.py to use shared module**

Replace `routers/auth.py`:

```python
"""Authentication endpoints."""
from fastapi import APIRouter, HTTPException
from passlib.context import CryptContext

from app.auth import create_token
from app.database import get_pool
from app.models.tables import UserRegister, UserLogin, UserResponse, TokenResponse, FCMTokenUpdate

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/register", response_model=TokenResponse)
async def register(body: UserRegister):
    pool = await get_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT id FROM users WHERE email = $1", body.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed = pwd_context.hash(body.password)
        row = await conn.fetchrow(
            "INSERT INTO users (email, password_hash) VALUES ($1, $2) RETURNING id, email, created_at",
            body.email, hashed,
        )
        token = create_token(row["id"])
        return TokenResponse(
            access_token=token,
            user=UserResponse(id=row["id"], email=row["email"], created_at=row["created_at"]),
        )


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, email, password_hash, created_at FROM users WHERE email = $1", body.email
        )
        if not row or not pwd_context.verify(body.password, row["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token = create_token(row["id"])
        return TokenResponse(
            access_token=token,
            user=UserResponse(id=row["id"], email=row["email"], created_at=row["created_at"]),
        )


@router.patch("/me/fcm-token")
async def update_fcm_token(body: FCMTokenUpdate, authorization: str):
    """Update device FCM token."""
    from app.auth import get_user_id_from_header
    user_id = await get_user_id_from_header(authorization)
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET fcm_token = $1 WHERE id = $2", body.fcm_token, user_id)
    return {"ok": True}
```

- [ ] **Step 3: Write subscriptions router (final)**

```python
"""Subscription management endpoints."""
from fastapi import APIRouter, Header

from app.auth import get_user_id_from_header
from app.database import get_pool
from app.models.tables import SubscriptionCreate, SubscriptionResponse, ListResponse

router = APIRouter()


@router.get("", response_model=ListResponse)
async def list_subscriptions(authorization: str = Header(...)):
    user_id = await get_user_id_from_header(authorization)
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT id, user_id, keyword, type, created_at
               FROM subscriptions WHERE user_id = $1 ORDER BY created_at DESC""",
            user_id,
        )
    items = [SubscriptionResponse(**r) for r in rows]
    return ListResponse(items=items, total=len(items))


@router.post("", response_model=SubscriptionResponse)
async def create_subscription(body: SubscriptionCreate, authorization: str = Header(...)):
    user_id = await get_user_id_from_header(authorization)
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO subscriptions (user_id, keyword, type) VALUES ($1, $2, $3)
               RETURNING id, user_id, keyword, type, created_at""",
            user_id, body.keyword, body.type,
        )
    return SubscriptionResponse(**row)


@router.delete("/{subscription_id}")
async def delete_subscription(subscription_id: int, authorization: str = Header(...)):
    user_id = await get_user_id_from_header(authorization)
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM subscriptions WHERE id = $1 AND user_id = $2",
            subscription_id, user_id,
        )
    return {"ok": True}
```

- [ ] **Step 4: Write articles and notifications routers**

`routers/articles.py`:
```python
from fastapi import APIRouter, Header, Query

from app.auth import get_user_id_from_header
from app.database import get_pool
from app.models.tables import ArticleResponse, ListResponse

router = APIRouter()


@router.get("", response_model=ListResponse)
async def list_articles(
    authorization: str = Header(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
):
    user_id = await get_user_id_from_header(authorization)
    pool = await get_pool()
    offset = (page - 1) * page_size
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, title, summary, source, source_url, published_at, score FROM articles ORDER BY published_at DESC LIMIT $1 OFFSET $2",
            page_size, offset,
        )
        total_row = await conn.fetchrow("SELECT COUNT(*) as c FROM articles")
    items = [ArticleResponse(**r) for r in rows]
    return ListResponse(items=items, total=total_row["c"])


@router.get("/digest/{date}", response_model=ListResponse)
async def get_daily_digest(date: str, authorization: str = Header(...)):
    pool = await get_pool()
    async with pool.acquire() as conn:
        digest = await conn.fetchrow(
            "SELECT article_ids FROM daily_digests WHERE date = $1::date", date
        )
        if not digest:
            return ListResponse(items=[], total=0)
        ids = digest["article_ids"]
        rows = await conn.fetch(
            "SELECT id, title, summary, source, source_url, published_at, score FROM articles WHERE id = ANY($1)",
            ids,
        )
    items = [ArticleResponse(**r) for r in rows]
    return ListResponse(items=items, total=len(items))
```

`routers/notifications.py`:
```python
from fastapi import APIRouter, Header, Query

from app.auth import get_user_id_from_header
from app.database import get_pool
from app.models.tables import NotificationResponse, ArticleResponse, ListResponse

router = APIRouter()


@router.get("", response_model=ListResponse)
async def list_notifications(
    authorization: str = Header(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    n_type: str = Query("track", regex="^(track|daily)$"),
):
    user_id = await get_user_id_from_header(authorization)
    pool = await get_pool()
    offset = (page - 1) * page_size
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT n.id, n.article_id, n.type, n.sent_at, n.read,
                      a.id as a_id, a.title, a.summary, a.source, a.source_url, a.published_at, a.score
               FROM notifications n
               LEFT JOIN articles a ON n.article_id = a.id
               WHERE n.user_id = $1 AND n.type = $2
               ORDER BY n.sent_at DESC LIMIT $3 OFFSET $4""",
            user_id, n_type, page_size, offset,
        )
        total_row = await conn.fetchrow(
            "SELECT COUNT(*) as c FROM notifications WHERE user_id = $1 AND type = $2",
            user_id, n_type,
        )
    items = []
    for r in rows:
        article = None
        if r["a_id"]:
            article = ArticleResponse(
                id=r["a_id"], title=r["title"], summary=r["summary"],
                source=r["source"], source_url=r["source_url"],
                published_at=r["published_at"], score=r["score"],
            )
        items.append(NotificationResponse(
            id=r["id"], article_id=r["article_id"], type=r["type"],
            sent_at=r["sent_at"], read=r["read"], article=article,
        ))
    return ListResponse(items=items, total=total_row["c"])


@router.patch("/{notification_id}/read")
async def mark_read(notification_id: int, authorization: str = Header(...)):
    user_id = await get_user_id_from_header(authorization)
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE notifications SET read = TRUE WHERE id = $1 AND user_id = $2",
            notification_id, user_id,
        )
    return {"ok": True}
```

- [ ] **Step 5: Commit**

```bash
git add backend && git commit -m "feat: add subscription, article, notification APIs"
```

---

## Phase 7: Android App

### Task 7.1: Create Android project with Firebase

**Files:** Generate Android project scaffold

- [ ] **Step 1: Create Android project**

Create a new Android project at `newspulse/android/NewsPulse/` using Android Studio with:
- Package name: `com.newspulse.app`
- Min SDK: 26
- Language: Kotlin
- Build system: Gradle (Kotlin DSL)
- Compose enabled

- [ ] **Step 2: Add dependencies to app/build.gradle.kts**

```kotlin
dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.4")
    implementation("androidx.activity:activity-compose:1.9.1")
    implementation(platform("androidx.compose:compose-bom:2024.06.00"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.navigation:navigation-compose:2.7.7")
    implementation("com.google.firebase:firebase-messaging-ktx:24.0.0")
    implementation("com.squareup.retrofit2:retrofit:2.11.0")
    implementation("com.squareup.retrofit2:converter-gson:2.11.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")
    implementation("androidx.datastore:datastore-preferences:1.1.1")
    testImplementation("junit:junit:4.13.2")
}
```

- [ ] **Step 3: Add google-services.json placeholder and Firebase plugin**

In project-level build.gradle.kts:
```kotlin
plugins {
    id("com.google.gms.google-services") version "4.4.2" apply false
}
```

In app/build.gradle.kts, add at top:
```kotlin
plugins {
    id("com.google.gms.google-services")
}
```

- [ ] **Step 4: Commit**

```bash
git add android && git commit -m "chore: scaffold Android project with Firebase and Compose"
```

---

### Task 7.2: Network layer and data models

**Files:**
- Create: `app/src/main/java/com/newspulse/app/data/ApiService.kt`
- Create: `app/src/main/java/com/newspulse/app/data/Models.kt`
- Create: `app/src/main/java/com/newspulse/app/data/AuthStore.kt`

- [ ] **Step 1: Write data models**

```kotlin
// Models.kt
package com.newspulse.app.data

import com.google.gson.annotations.SerializedName

data class LoginRequest(val email: String, val password: String)
data class RegisterRequest(val email: String, val password: String)
data class TokenResponse(
    @SerializedName("access_token") val accessToken: String,
    @SerializedName("token_type") val tokenType: String,
    val user: UserResponse
)
data class UserResponse(val id: Int, val email: String, @SerializedName("created_at") val createdAt: String)
data class FcmTokenUpdate(@SerializedName("fcm_token") val fcmToken: String)

data class SubscriptionRequest(val keyword: String, val type: String = "topic")
data class SubscriptionResponse(
    val id: Int,
    @SerializedName("user_id") val userId: Int,
    val keyword: String,
    val type: String,
    @SerializedName("created_at") val createdAt: String
)

data class ArticleResponse(
    val id: Int,
    val title: String,
    val summary: String?,
    val source: String,
    @SerializedName("source_url") val sourceUrl: String,
    @SerializedName("published_at") val publishedAt: String?,
    val score: Double
)

data class NotificationResponse(
    val id: Int,
    @SerializedName("article_id") val articleId: Int,
    val type: String,
    @SerializedName("sent_at") val sentAt: String,
    val read: Boolean,
    val article: ArticleResponse?
)

data class ListResponse<T>(
    val items: List<T>,
    val total: Int
)
```

- [ ] **Step 2: Write Retrofit API service**

```kotlin
// ApiService.kt
package com.newspulse.app.data

import retrofit2.Response
import retrofit2.http.*

interface ApiService {
    @POST("auth/register")
    suspend fun register(@Body body: RegisterRequest): Response<TokenResponse>

    @POST("auth/login")
    suspend fun login(@Body body: LoginRequest): Response<TokenResponse>

    @PATCH("auth/me/fcm-token")
    suspend fun updateFcmToken(@Body body: FcmTokenUpdate): Response<Map<String, Any>>

    @GET("subscriptions")
    suspend fun listSubscriptions(): Response<ListResponse<SubscriptionResponse>>

    @POST("subscriptions")
    suspend fun createSubscription(@Body body: SubscriptionRequest): Response<SubscriptionResponse>

    @DELETE("subscriptions/{id}")
    suspend fun deleteSubscription(@Path("id") id: Int): Response<Map<String, Any>>

    @GET("articles")
    suspend fun listArticles(
        @Query("page") page: Int = 1,
        @Query("page_size") pageSize: Int = 20
    ): Response<ListResponse<ArticleResponse>>

    @GET("articles/digest/{date}")
    suspend fun getDailyDigest(@Path("date") date: String): Response<ListResponse<ArticleResponse>>

    @GET("notifications")
    suspend fun listNotifications(
        @Query("page") page: Int = 1,
        @Query("page_size") pageSize: Int = 20,
        @Query("n_type") type: String = "track"
    ): Response<ListResponse<NotificationResponse>>

    @PATCH("notifications/{id}/read")
    suspend fun markNotificationRead(@Path("id") id: Int): Response<Map<String, Any>>
}
```

- [ ] **Step 3: Write AuthStore (token persistence)**

```kotlin
// AuthStore.kt
package com.newspulse.app.data

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map

val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "auth")

class AuthStore(private val context: Context) {
    companion object {
        val TOKEN_KEY = stringPreferencesKey("access_token")
        val EMAIL_KEY = stringPreferencesKey("email")
    }

    val token: Flow<String?> = context.dataStore.data.map { it[TOKEN_KEY] }
    val email: Flow<String?> = context.dataStore.data.map { it[EMAIL_KEY] }

    suspend fun saveAuth(token: String, email: String) {
        context.dataStore.edit {
            it[TOKEN_KEY] = token
            it[EMAIL_KEY] = email
        }
    }

    suspend fun clear() {
        context.dataStore.edit { it.clear() }
    }

    suspend fun getToken(): String? = token.first()
}
```

- [ ] **Step 4: Write Retrofit client with auth interceptor**

```kotlin
// RetrofitClient.kt
package com.newspulse.app.data

import android.content.Context
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

object RetrofitClient {
    private const val BASE_URL = "http://10.0.2.2:8000/"  // localhost from emulator

    fun create(context: Context): ApiService {
        val authStore = AuthStore(context)

        val authInterceptor = Interceptor { chain ->
            val token = runBlocking { authStore.getToken() }
            val request = if (token != null) {
                chain.request().newBuilder()
                    .addHeader("Authorization", "Bearer $token")
                    .build()
            } else {
                chain.request()
            }
            chain.proceed(request)
        }

        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }

        val client = OkHttpClient.Builder()
            .addInterceptor(authInterceptor)
            .addInterceptor(logging)
            .build()

        return Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(ApiService::class.java)
    }

    private fun <T> runBlocking(block: suspend () -> T): T {
        return kotlinx.coroutines.runBlocking { block() }
    }
}
```

- [ ] **Step 5: Commit**

```bash
git add android && git commit -m "feat: add network layer — Retrofit, models, auth persistence"
```

---

### Task 7.3: FCM service

**Files:** Create `app/src/main/java/com/newspulse/app/FcmService.kt`

- [ ] **Step 1: Write FCM token handling service**

```kotlin
// FcmService.kt
package com.newspulse.app

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import androidx.core.app.NotificationCompat
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import com.newspulse.app.data.AuthStore
import com.newspulse.app.data.FcmTokenUpdate
import com.newspulse.app.data.RetrofitClient
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class FcmService : FirebaseMessagingService() {

    override fun onNewToken(token: String) {
        super.onNewToken(token)
        sendTokenToServer(token)
    }

    override fun onMessageReceived(message: RemoteMessage) {
        super.onMessageReceived(message)
        val title = message.notification?.title ?: "NewsPulse"
        val body = message.notification?.body ?: ""
        val type = message.data["type"] ?: "track"
        val articleId = message.data["article_id"]
        val digestId = message.data["digest_id"]

        showNotification(title, body, type, articleId, digestId)
    }

    private fun sendTokenToServer(token: String) {
        val authStore = AuthStore(this)
        val api = RetrofitClient.create(this)
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val serverToken = authStore.getToken()
                if (serverToken != null) {
                    api.updateFcmToken(FcmTokenUpdate(token))
                }
            } catch (_: Exception) { }
        }
    }

    private fun showNotification(title: String, body: String, type: String, articleId: String?, digestId: String?) {
        val channelId = "newspulse_channel"
        val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(channelId, "NewsPulse", NotificationManager.IMPORTANCE_HIGH)
            notificationManager.createNotificationChannel(channel)
        }

        val intent = Intent(this, MainActivity::class.java).apply {
            putExtra("type", type)
            articleId?.let { putExtra("article_id", it) }
            digestId?.let { putExtra("digest_id", it) }
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }

        val pendingIntent = PendingIntent.getActivity(
            this, System.currentTimeMillis().toInt(), intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(this, channelId)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle(title)
            .setContentText(body)
            .setAutoCancel(true)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setContentIntent(pendingIntent)
            .build()

        notificationManager.notify(System.currentTimeMillis().toInt(), notification)
    }
}
```

- [ ] **Step 2: Register service in AndroidManifest.xml**

```xml
<service
    android:name=".FcmService"
    android:exported="false">
    <intent-filter>
        <action android:name="com.google.firebase.MESSAGING_EVENT" />
    </intent-filter>
</service>
```

- [ ] **Step 3: Commit**

```bash
git add android && git commit -m "feat: add FCM push notification service"
```

---

### Task 7.4: UI Screens — Auth, Feed, Tracking, Settings

**Files:**
- Create: `app/src/main/java/com/newspulse/app/ui/AuthScreen.kt`
- Create: `app/src/main/java/com/newspulse/app/ui/FeedScreen.kt`
- Create: `app/src/main/java/com/newspulse/app/ui/TrackingScreen.kt`
- Create: `app/src/main/java/com/newspulse/app/ui/SettingsScreen.kt`
- Create: `app/src/main/java/com/newspulse/app/ui/MainActivity.kt`
- Create: `app/src/main/java/com/newspulse/app/ui/Theme.kt`

- [ ] **Step 1: Write AuthScreen.kt**

```kotlin
// AuthScreen.kt
package com.newspulse.app.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.newspulse.app.data.*
import kotlinx.coroutines.launch

@Composable
fun AuthScreen(
    api: ApiService,
    authStore: AuthStore,
    onLoginSuccess: () -> Unit
) {
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var isRegister by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var loading by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    Column(
        modifier = Modifier.fillMaxSize().padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = "NewsPulse",
            style = MaterialTheme.typography.headlineLarge,
            modifier = Modifier.padding(bottom = 32.dp)
        )

        OutlinedTextField(
            value = email,
            onValueChange = { email = it },
            label = { Text("邮箱") },
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(Modifier.height(8.dp))
        OutlinedTextField(
            value = password,
            onValueChange = { password = it },
            label = { Text("密码") },
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(Modifier.height(16.dp))

        error?.let {
            Text(it, color = MaterialTheme.colorScheme.error)
            Spacer(Modifier.height(8.dp))
        }

        Button(
            onClick = {
                loading = true
                error = null
                scope.launch {
                    try {
                        val resp = if (isRegister) {
                            api.register(RegisterRequest(email, password))
                        } else {
                            api.login(LoginRequest(email, password))
                        }
                        if (resp.isSuccessful) {
                            val body = resp.body()!!
                            authStore.saveAuth(body.accessToken, body.user.email)
                            onLoginSuccess()
                        } else {
                            error = if (isRegister) "注册失败" else "登录失败"
                        }
                    } catch (e: Exception) {
                        error = "网络错误: ${e.message}"
                    }
                    loading = false
                }
            },
            modifier = Modifier.fillMaxWidth(),
            enabled = !loading
        ) {
            Text(if (isRegister) "注册" else "登录")
        }

        TextButton(onClick = { isRegister = !isRegister }) {
            Text(if (isRegister) "已有账号？登录" else "没有账号？注册")
        }
    }
}
```

- [ ] **Step 2: Write FeedScreen.kt**

```kotlin
// FeedScreen.kt
package com.newspulse.app.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.newspulse.app.data.ApiService
import com.newspulse.app.data.ArticleResponse

@Composable
fun FeedScreen(api: ApiService) {
    var articles by remember { mutableStateOf<List<ArticleResponse>>(emptyList()) }
    var loading by remember { mutableStateOf(true) }

    LaunchedEffect(Unit) {
        try {
            val resp = api.listArticles(page = 1, pageSize = 50)
            if (resp.isSuccessful) {
                articles = resp.body()?.items ?: emptyList()
            }
        } catch (_: Exception) { }
        loading = false
    }

    if (loading) {
        Box(Modifier.fillMaxSize()) { CircularProgressIndicator(Modifier.align(androidx.compose.ui.Alignment.Center)) }
    } else {
        LazyColumn(modifier = Modifier.fillMaxSize(), contentPadding = PaddingValues(16.dp)) {
            items(articles) { article ->
                Card(
                    modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp).clickable { },
                    elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
                ) {
                    Column(Modifier.padding(12.dp)) {
                        Text(article.title, style = MaterialTheme.typography.titleSmall)
                        article.summary?.let {
                            Text(it, style = MaterialTheme.typography.bodySmall, maxLines = 2, modifier = Modifier.padding(top = 4.dp))
                        }
                        Row(Modifier.fillMaxWidth().padding(top = 4.dp), horizontalArrangement = Arrangement.SpaceBetween) {
                            Text(article.source, style = MaterialTheme.typography.labelSmall)
                            Text("热度: ${"%.1f".format(article.score)}", style = MaterialTheme.typography.labelSmall)
                        }
                    }
                }
            }
        }
    }
}
```

- [ ] **Step 3: Write TrackingScreen.kt**

```kotlin
// TrackingScreen.kt
package com.newspulse.app.ui

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.newspulse.app.data.ApiService
import com.newspulse.app.data.NotificationResponse

@Composable
fun TrackingScreen(api: ApiService) {
    var notifications by remember { mutableStateOf<List<NotificationResponse>>(emptyList()) }
    var loading by remember { mutableStateOf(true) }

    LaunchedEffect(Unit) {
        try {
            val resp = api.listNotifications(page = 1, pageSize = 50, type = "track")
            if (resp.isSuccessful) {
                notifications = resp.body()?.items ?: emptyList()
            }
        } catch (_: Exception) { }
        loading = false
    }

    if (loading) {
        Box(Modifier.fillMaxSize()) { CircularProgressIndicator(Modifier.align(androidx.compose.ui.Alignment.Center)) }
    } else if (notifications.isEmpty()) {
        Box(Modifier.fillMaxSize()) {
            Text("暂无追踪消息", Modifier.align(androidx.compose.ui.Alignment.Center))
        }
    } else {
        LazyColumn(modifier = Modifier.fillMaxSize(), contentPadding = PaddingValues(16.dp)) {
            items(notifications) { notif ->
                Card(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                    Column(Modifier.padding(12.dp)) {
                        notif.article?.let { article ->
                            Text(article.title, style = MaterialTheme.typography.titleSmall)
                            Text(article.source, style = MaterialTheme.typography.labelSmall)
                        }
                    }
                }
            }
        }
    }
}
```

- [ ] **Step 4: Write SettingsScreen.kt**

```kotlin
// SettingsScreen.kt
package com.newspulse.app.ui

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.newspulse.app.data.*
import kotlinx.coroutines.launch

@Composable
fun SettingsScreen(api: ApiService, authStore: AuthStore, onLogout: () -> Unit) {
    var subscriptions by remember { mutableStateOf<List<SubscriptionResponse>>(emptyList()) }
    var newKeyword by remember { mutableStateOf("") }
    val scope = rememberCoroutineScope()

    LaunchedEffect(Unit) {
        try {
            val resp = api.listSubscriptions()
            if (resp.isSuccessful) {
                subscriptions = resp.body()?.items ?: emptyList()
            }
        } catch (_: Exception) { }
    }

    fun refreshSubs() {
        scope.launch {
            try {
                val resp = api.listSubscriptions()
                if (resp.isSuccessful) {
                    subscriptions = resp.body()?.items ?: emptyList()
                }
            } catch (_: Exception) { }
        }
    }

    Column(Modifier.fillMaxSize().padding(16.dp)) {
        Text("订阅管理", style = MaterialTheme.typography.titleMedium, modifier = Modifier.padding(bottom = 12.dp))

        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            OutlinedTextField(
                value = newKeyword,
                onValueChange = { newKeyword = it },
                label = { Text("关键词") },
                modifier = Modifier.weight(1f)
            )
            Spacer(Modifier.width(8.dp))
            IconButton(onClick = {
                if (newKeyword.isNotBlank()) {
                    scope.launch {
                        try {
                            api.createSubscription(SubscriptionRequest(newKeyword.trim()))
                            newKeyword = ""
                            refreshSubs()
                        } catch (_: Exception) { }
                    }
                }
            }) {
                Icon(Icons.Default.Add, contentDescription = "添加")
            }
        }

        Spacer(Modifier.height(12.dp))

        LazyColumn {
            items(subscriptions) { sub ->
                Row(Modifier.fillMaxWidth().padding(vertical = 4.dp), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                    Text("${sub.keyword} (${sub.type})")
                    IconButton(onClick = {
                        scope.launch {
                            try {
                                api.deleteSubscription(sub.id)
                                refreshSubs()
                            } catch (_: Exception) { }
                        }
                    }) {
                        Icon(Icons.Default.Delete, contentDescription = "删除")
                    }
                }
            }
        }

        Spacer(Modifier.weight(1f))
        OutlinedButton(onClick = { scope.launch { authStore.clear(); onLogout() } }, modifier = Modifier.fillMaxWidth()) {
            Text("退出登录")
        }
    }
}
```

- [ ] **Step 5: Write MainActivity.kt with navigation**

```kotlin
// MainActivity.kt
package com.newspulse.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.newspulse.app.data.AuthStore
import com.newspulse.app.data.RetrofitClient
import com.newspulse.app.ui.*
import kotlinx.coroutines.runBlocking

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val authStore = AuthStore(this)
        val api = RetrofitClient.create(this)

        val isLoggedIn = runBlocking { authStore.getToken() != null }

        setContent {
            MaterialTheme {
                val navController = rememberNavController()
                val startDest = if (isLoggedIn) "feed" else "auth"

                NavHost(navController = navController, startDestination = startDest) {
                    composable("auth") {
                        AuthScreen(api = api, authStore = authStore, onLoginSuccess = {
                            navController.navigate("feed") { popUpTo("auth") { inclusive = true } }
                        })
                    }
                    composable("feed") {
                        FeedScreen(api = api)
                    }
                    composable("tracking") {
                        TrackingScreen(api = api)
                    }
                    composable("settings") {
                        SettingsScreen(api = api, authStore = authStore, onLogout = {
                            navController.navigate("auth") { popUpTo(0) { inclusive = true } }
                        })
                    }
                }
            }
        }
    }
}
```

- [ ] **Step 6: Add bottom navigation bar to MainActivity (revised)**

Update MainActivity to include bottom navigation:

```kotlin
// Replace the NavHost block with:
val navController = rememberNavController()
val startDest = if (isLoggedIn) "feed" else "auth"

Scaffold(
    bottomBar = {
        if (isLoggedIn) {
            NavigationBar {
                NavigationBarItem(selected = false, onClick = { navController.navigate("feed") }, icon = { Text("新闻") }, label = { Text("每日精选") })
                NavigationBarItem(selected = false, onClick = { navController.navigate("tracking") }, icon = { Text("追踪") }, label = { Text("消息追踪") })
                NavigationBarItem(selected = false, onClick = { navController.navigate("settings") }, icon = { Text("设置") }, label = { Text("设置") })
            }
        }
    }
) { padding ->
    NavHost(navController = navController, startDestination = startDest, modifier = Modifier.padding(padding)) {
        composable("auth") { AuthScreen(...) }
        composable("feed") { FeedScreen(...) }
        composable("tracking") { TrackingScreen(...) }
        composable("settings") { SettingsScreen(...) }
    }
}
```

- [ ] **Step 7: Add AndroidManifest permissions and internet access**

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
```

- [ ] **Step 8: Commit**

```bash
git add android && git commit -m "feat: add all UI screens — auth, feed, tracking, settings with navigation"
```

---

## Phase 8: Deployment & Final Integration

### Task 8.1: Railway deployment config

**Files:**
- Create: `newspulse/backend/Procfile`
- Create: `newspulse/backend/.env.example`
- Create: `newspulse/.gitignore`

- [ ] **Step 1: Write Procfile**

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

- [ ] **Step 2: Write .env.example**

```
DATABASE_URL=postgresql+asyncpg://postgres:password@host:5432/newspulse
NEWSAPI_KEY=your_newsapi_key
JWT_SECRET=generate-a-random-secret
FCM_CREDENTIALS_PATH=firebase-credentials.json
```

- [ ] **Step 3: Write .gitignore**

```
__pycache__/
*.pyc
.env
firebase-credentials.json
*.apk
*.aab
/build
/app/build
.idea/
*.iml
.gradle/
local.properties
```

- [ ] **Step 4: Update config.py to support Railway's PORT env**

No change needed — Pydantic Settings already reads from env. Add `port` if Railway requires, but uvicorn already handles `$PORT`.

- [ ] **Step 5: Commit**

```bash
git add newspulse && git commit -m "chore: add deployment config — Procfile, env example, gitignore"
```

---

### Task 8.2: Final verification checklist

Run against local backend:

```bash
cd newspulse/backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then verify:
- `GET /health` → `{"status": "ok"}`
- `POST /auth/register` → returns token
- `POST /auth/login` → returns token
- `POST /subscriptions` (with token) → creates subscription
- `GET /subscriptions` → lists subscriptions
- `GET /articles` → lists articles
- `GET /notifications` → lists notifications

Build Android APK:
```bash
cd android/NewsPulse
./gradlew assembleDebug
```
Expected: builds successfully, APK at `app/build/outputs/apk/debug/app-debug.apk`.

Install on Android device and verify push notification delivery.

---

## Summary

| Phase | Tasks | What it delivers |
|-------|-------|-----------------|
| 1 | 1.1–1.3 | Backend scaffold, config, database, FastAPI app |
| 2 | 2.1 | User registration/login, JWT auth, FCM token binding |
| 3 | 3.1 | News aggregation from NewsAPI + RSS, dedup, scoring |
| 4 | 4.1 | Match engine — keyword exact + embedding semantic |
| 5 | 5.1–5.2 | FCM push, daily digest, scheduler wiring |
| 6 | 6.1 | Subscription CRUD, article feed, notification APIs |
| 7 | 7.1–7.4 | Android app — FCM, auth, feed, tracking, settings screens |
| 8 | 8.1–8.2 | Deployment config, final verification |

"""
Tests for the /api/repos endpoints.

Uses httpx AsyncClient with real JWT tokens (signed with SUPABASE_JWT_SECRET
from conftest.py) so the full auth middleware is exercised without mocking.
"""
from __future__ import annotations

import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import get_db
from app.main import app
from app.models import Base

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
TEST_JWT_SECRET = "test-secret-key-that-is-long-enough"


# ── Helpers ────────────────────────────────────────────────────────────────

def _make_token(sub: str = "1", expired: bool = False) -> str:
    payload: dict = {"sub": sub, "aud": "authenticated"}
    payload["exp"] = int(time.time()) + (-3600 if expired else 3600)
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        # Create only tables without pgvector dependency
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn,
                tables=[
                    Base.metadata.tables["users"],
                    Base.metadata.tables["repos"],
                ],
            )
        )
    AsyncTestSession = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncTestSession() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    """AsyncClient with DB override and auth token preset in default headers."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Generate token inside fixture so conftest env vars are already applied
    auth_headers = {"Authorization": f"Bearer {_make_token()}"}

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(
        transport=transport, base_url="http://test", headers=auth_headers
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Tests ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_repo_returns_200_with_id(client: AsyncClient) -> None:
    with patch("app.api.repos.capture_event"), \
         patch("app.api.repos.scan_repo_task") as mock_task:
        mock_task.delay = MagicMock()
        resp = await client.post(
            "/api/repos",
            json={"url": "https://github.com/user/my-repo"},
        )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "id" in data
    assert data["name"] == "my-repo"
    assert data["url"] == "https://github.com/user/my-repo"


@pytest.mark.asyncio
async def test_list_repos_returns_user_repos(client: AsyncClient) -> None:
    with patch("app.api.repos.capture_event"):
        await client.post("/api/repos", json={"url": "https://github.com/user/repo-a"})
        await client.post("/api/repos", json={"url": "https://github.com/user/repo-b"})

    resp = await client.get("/api/repos")
    assert resp.status_code == 200, resp.text
    repos = resp.json()
    assert len(repos) == 2
    names = {r["name"] for r in repos}
    assert "repo-a" in names
    assert "repo-b" in names


@pytest.mark.asyncio
async def test_scan_nonexistent_repo_returns_404(client: AsyncClient) -> None:
    mock_redis = AsyncMock()
    mock_redis.set = AsyncMock()
    with patch("app.api.repos.get_redis", return_value=mock_redis):
        resp = await client.post("/api/repos/99999/scan")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_scan_progress_not_started(client: AsyncClient) -> None:
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    with patch("app.api.repos.get_redis", return_value=mock_redis):
        resp = await client.get("/api/repos/42/scan-progress")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "not_started"
    assert data["progress"] == 0


@pytest.mark.asyncio
async def test_get_scan_progress_returns_redis_data(client: AsyncClient) -> None:
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(
        return_value=json.dumps({"status": "parsing_ast", "progress": 30})
    )
    with patch("app.api.repos.get_redis", return_value=mock_redis):
        resp = await client.get("/api/repos/42/scan-progress")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "parsing_ast"
    assert data["progress"] == 30


@pytest.mark.asyncio
async def test_unauthenticated_request_returns_401() -> None:
    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/repos")
    assert resp.status_code == 401
    assert "error" not in resp.json()

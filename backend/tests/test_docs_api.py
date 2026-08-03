from __future__ import annotations

import time
from unittest.mock import MagicMock
import jwt
import pytest
import pytest_asyncio
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import get_db
from app.main import app
from app.models import Base, Endpoint, Repo
from app.api.docs import get_openapi_docs, export_docs, _get_user_id, _parse_user_id_int

TEST_DB_URL = "sqlite+aiosqlite:///:memory:?cache=shared"

engine = create_async_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)
AsyncTestSession = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def _make_token(sub: str = "1", expired: bool = False) -> str:
    payload: dict = {"sub": sub, "aud": "authenticated"}
    payload["exp"] = int(time.time()) + (-3600 if expired else 3600)
    return jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")


@pytest_asyncio.fixture(scope="module", autouse=True)
async def prepare_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    async with AsyncTestSession() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    auth_headers = {"Authorization": f"Bearer {_make_token()}"}
    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(
        transport=transport, base_url="http://test", headers=auth_headers
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_repo(db_session: AsyncSession):
    repo = Repo(github_repo_id="123", name="test-repo", url="http://github.com/test", user_id=1)
    db_session.add(repo)
    await db_session.commit()
    await db_session.refresh(repo)
    return repo


@pytest_asyncio.fixture
async def sample_approved_endpoint(db_session: AsyncSession, sample_repo: Repo):
    ep = Endpoint(
        repo_id=sample_repo.id,
        method="GET",
        path="/api/test",
        handler_function="test_fn",
        file_path="main.py",
        line_number=1,
        status="approved",
        quality_score=8.0,
        attempts=1,
        needs_human_review=False,
        source_code_snippet="def test_fn(): pass",
        generated_doc_json={
            "title": "Test doc",
            "description": "Test description",
            "parameters": [{"name": "q", "in": "query"}],
            "request_body": {"type": "object", "properties": {"a": {"type": "string"}}},
            "responses": [{"status": 200, "description": "OK"}],
        },
    )
    db_session.add(ep)
    await db_session.commit()
    await db_session.refresh(ep)
    return ep


# ── Unit tests for route functions ────────────────────────────────────────

def test_docs_helpers():
    req = MagicMock()
    req.state.user_id = "1"
    assert _get_user_id(req) == "1"
    assert _parse_user_id_int("1") == 1
    with pytest.raises(HTTPException):
        _parse_user_id_int("abc")

    unauth = MagicMock()
    unauth.state.user_id = None
    with pytest.raises(HTTPException):
        _get_user_id(unauth)


@pytest.mark.asyncio
async def test_direct_get_openapi_docs(db_session: AsyncSession, sample_repo: Repo, sample_approved_endpoint: Endpoint):
    req = MagicMock()
    req.state.user_id = "1"

    spec = await get_openapi_docs(repo_id=str(sample_repo.id), request=req, db=db_session)
    assert spec["openapi"] == "3.1.0"
    assert "/api/test" in spec["paths"]

    with pytest.raises(HTTPException):
        await get_openapi_docs(repo_id="invalid", request=req, db=db_session)

    with pytest.raises(HTTPException):
        await get_openapi_docs(repo_id="99999", request=req, db=db_session)


@pytest.mark.asyncio
async def test_direct_export_docs(db_session: AsyncSession, sample_repo: Repo, sample_approved_endpoint: Endpoint):
    req = MagicMock()
    req.state.user_id = "1"

    res = await export_docs(repo_id=str(sample_repo.id), request=req, format="markdown", db=db_session)
    assert "text/markdown" in res.media_type
    assert "GET /api/test" in res.body.decode()

    with pytest.raises(HTTPException):
        await export_docs(repo_id=str(sample_repo.id), request=req, format="pdf", db=db_session)

    with pytest.raises(HTTPException):
        await export_docs(repo_id="invalid", request=req, format="markdown", db=db_session)

    with pytest.raises(HTTPException):
        await export_docs(repo_id="99999", request=req, format="markdown", db=db_session)

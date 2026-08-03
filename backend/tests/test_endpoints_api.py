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
from app.api.endpoints import (
    list_endpoints,
    approve_endpoint,
    reject_endpoint,
    update_endpoint_doc,
    bulk_approve_endpoints,
    _get_user_id,
    _parse_user_id_int,
)
from app.models.schemas import EndpointUpdateRequest, BulkApproveRequest

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
async def sample_endpoint(db_session: AsyncSession, sample_repo: Repo):
    ep = Endpoint(
        repo_id=sample_repo.id,
        method="GET",
        path="/api/test",
        handler_function="test_fn",
        file_path="main.py",
        line_number=1,
        status="pending",
        quality_score=8.0,
        attempts=1,
        needs_human_review=True,
        source_code_snippet="def test_fn(): pass",
    )
    db_session.add(ep)
    await db_session.commit()
    await db_session.refresh(ep)
    return ep


# ── Unit tests for route functions ────────────────────────────────────────

def test_get_user_id_helpers():
    req = MagicMock()
    req.state.user_id = "123"
    assert _get_user_id(req) == "123"
    assert _parse_user_id_int("123") == 123
    with pytest.raises(HTTPException):
        _parse_user_id_int("invalid")

    unauth_req = MagicMock()
    unauth_req.state.user_id = None
    with pytest.raises(HTTPException):
        _get_user_id(unauth_req)


@pytest.mark.asyncio
async def test_direct_list_endpoints(db_session: AsyncSession, sample_repo: Repo, sample_endpoint: Endpoint):
    req = MagicMock()
    req.state.user_id = "1"

    eps = await list_endpoints(repo_id=str(sample_repo.id), request=req, db=db_session)
    assert len(eps) >= 1

    eps_filtered = await list_endpoints(repo_id=str(sample_repo.id), request=req, status="pending", file_path="main.py", db=db_session)
    assert len(eps_filtered) >= 1

    with pytest.raises(HTTPException):
        await list_endpoints(repo_id="invalid", request=req, db=db_session)

    with pytest.raises(HTTPException):
        await list_endpoints(repo_id="99999", request=req, db=db_session)


@pytest.mark.asyncio
async def test_direct_approve_endpoint(db_session: AsyncSession, sample_endpoint: Endpoint):
    req = MagicMock()
    req.state.user_id = "1"

    ep = await approve_endpoint(endpoint_id=sample_endpoint.id, request=req, db=db_session)
    assert ep.status == "approved"
    assert ep.needs_human_review is False

    with pytest.raises(HTTPException):
        await approve_endpoint(endpoint_id=99999, request=req, db=db_session)


@pytest.mark.asyncio
async def test_direct_reject_endpoint(db_session: AsyncSession, sample_endpoint: Endpoint):
    req = MagicMock()
    req.state.user_id = "1"

    ep = await reject_endpoint(endpoint_id=sample_endpoint.id, request=req, db=db_session)
    assert ep.status == "rejected"
    assert ep.needs_human_review is True

    with pytest.raises(HTTPException):
        await reject_endpoint(endpoint_id=99999, request=req, db=db_session)


@pytest.mark.asyncio
async def test_direct_update_endpoint_doc(db_session: AsyncSession, sample_endpoint: Endpoint):
    req = MagicMock()
    req.state.user_id = "1"

    update_req = EndpointUpdateRequest(title="Updated Title", description="Updated Desc")
    ep = await update_endpoint_doc(endpoint_id=sample_endpoint.id, req=update_req, request=req, db=db_session)
    assert ep.generated_doc_json["title"] == "Updated Title"

    with pytest.raises(HTTPException):
        await update_endpoint_doc(endpoint_id=99999, req=update_req, request=req, db=db_session)


@pytest.mark.asyncio
async def test_direct_bulk_approve(db_session: AsyncSession, sample_repo: Repo, sample_endpoint: Endpoint):
    req = MagicMock()
    req.state.user_id = "1"

    bulk_req = BulkApproveRequest(min_quality_score=7.0)
    resp = await bulk_approve_endpoints(repo_id=str(sample_repo.id), req=bulk_req, request=req, db=db_session)
    assert resp.approved_count >= 1

    with pytest.raises(HTTPException):
        await bulk_approve_endpoints(repo_id="invalid", req=bulk_req, request=req, db=db_session)

    with pytest.raises(HTTPException):
        await bulk_approve_endpoints(repo_id="99999", req=bulk_req, request=req, db=db_session)

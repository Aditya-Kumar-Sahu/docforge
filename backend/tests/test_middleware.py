"""
Tests for CoreMiddleware: JWT validation, error masking, user_id on request state.

Uses TestClient which exercises the full Starlette middleware stack.
The JWT secret in tests is "test-secret" — tokens are signed with HS256.
"""
import time
import pytest
import jwt
from fastapi.testclient import TestClient
from fastapi import FastAPI, Request

from app.core.middleware import CoreMiddleware
from app.core.config import settings


# ── Helpers ────────────────────────────────────────────────────────────────

def _make_token(sub: str = "user-123", expired: bool = False) -> str:
    payload: dict = {
        "sub": sub,
        "aud": "authenticated",
    }
    if expired:
        payload["exp"] = int(time.time()) - 3600
    else:
        payload["exp"] = int(time.time()) + 3600
    return jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")


def _make_test_app() -> FastAPI:
    """Minimal app with the CoreMiddleware and a protected /api/me route."""
    app = FastAPI()
    app.add_middleware(CoreMiddleware)

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    @app.get("/api/me")
    async def me(request: Request) -> dict:
        return {"user_id": request.state.user_id}

    return app


# ── Tests ──────────────────────────────────────────────────────────────────

@pytest.fixture
def client() -> TestClient:
    return TestClient(_make_test_app(), raise_server_exceptions=False)


def test_public_health_endpoint_requires_no_token(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200


def test_protected_route_requires_authorization_header(client: TestClient) -> None:
    resp = client.get("/api/me")
    assert resp.status_code == 401
    # Must NOT leak internal error details
    body = resp.json()
    assert "error" not in body
    assert "detail" in body


def test_invalid_token_returns_401_without_leaking_error(client: TestClient) -> None:
    resp = client.get("/api/me", headers={"Authorization": "Bearer not.a.real.token"})
    assert resp.status_code == 401
    body = resp.json()
    assert "error" not in body
    assert "traceback" not in str(body).lower()


def test_expired_token_returns_401(client: TestClient) -> None:
    token = _make_token(expired=True)
    resp = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert resp.json().get("detail") == "Token has expired"


def test_valid_token_sets_user_id_on_request_state(client: TestClient) -> None:
    token = _make_token(sub="user-abc")
    resp = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["user_id"] == "user-abc"


def test_malformed_authorization_header_returns_401(client: TestClient) -> None:
    # Missing "Bearer " prefix
    resp = client.get("/api/me", headers={"Authorization": "Token abcdef"})
    assert resp.status_code == 401

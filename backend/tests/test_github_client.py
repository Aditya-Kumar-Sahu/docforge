"""
Tests for GitHubAppClient.

The test RSA key is generated at module load time and injected into settings
via os.environ before the app module is imported. GITHUB_APP_ID is set in
conftest.py; GITHUB_APP_PRIVATE_KEY is overridden here with a test key.
"""
import os
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
)


def _generate_test_private_key() -> str:
    """Generate a test RSA 2048-bit private key in PEM/PKCS8 format."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()).decode()


# Generate key and inject into env BEFORE importing any app module.
# conftest.py sets GITHUB_APP_PRIVATE_KEY="" — we override here with a real key.
_TEST_KEY = _generate_test_private_key()
os.environ["GITHUB_APP_PRIVATE_KEY"] = _TEST_KEY.replace("\n", "\\n")
os.environ["GITHUB_APP_ID"] = "12345"

from app.core.github_client import GitHubAppClient  # noqa: E402


@pytest.fixture()
def gh_client() -> GitHubAppClient:
    """Fresh GitHubAppClient with empty token cache for each test."""
    return GitHubAppClient()


# ── JWT generation ─────────────────────────────────────────────────────────


def test_generate_app_jwt_has_correct_claims(gh_client: GitHubAppClient) -> None:
    """JWT must contain iss=app_id, iat, and exp claims, using RS256."""
    token = gh_client._generate_app_jwt()
    decoded = jwt.decode(token, options={"verify_signature": False})
    assert decoded["iss"] == "12345"
    assert "iat" in decoded
    assert "exp" in decoded
    # exp must be ≤ 10 minutes from now
    import time
    assert decoded["exp"] - int(time.time()) <= 10 * 60


# ── Installation token caching ─────────────────────────────────────────────


@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_get_installation_token_calls_github_once(
    mock_client_cls: MagicMock, gh_client: GitHubAppClient
) -> None:
    """First call fetches token from GitHub; second call hits cache."""
    mock_http = AsyncMock()
    mock_client_cls.return_value.__aenter__.return_value = mock_http

    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "token": "ghs_testtoken",
        "expires_at": "2030-01-01T00:00:00Z",
    }
    mock_http.post.return_value = mock_resp

    token1 = await gh_client._get_installation_token(123)
    assert token1 == "ghs_testtoken"
    mock_http.post.assert_called_once()

    # Second call — should NOT hit GitHub again
    mock_http.post.reset_mock()
    token2 = await gh_client._get_installation_token(123)
    assert token2 == "ghs_testtoken"
    mock_http.post.assert_not_called()


@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_get_installation_token_refreshes_near_expiry(
    mock_client_cls: MagicMock, gh_client: GitHubAppClient
) -> None:
    """Token near expiry (< 60s) triggers a refresh call to GitHub."""
    import time

    # Seed the cache with a token that expires in 30s (below the 60s buffer)
    gh_client._installation_tokens[456] = ("old_token", time.time() + 30)

    mock_http = AsyncMock()
    mock_client_cls.return_value.__aenter__.return_value = mock_http
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "token": "ghs_newtoken",
        "expires_at": "2030-01-01T00:00:00Z",
    }
    mock_http.post.return_value = mock_resp

    token = await gh_client._get_installation_token(456)
    assert token == "ghs_newtoken"
    mock_http.post.assert_called_once()


# ── API methods ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_get_pr_files_returns_file_list(
    mock_client_cls: MagicMock, gh_client: GitHubAppClient
) -> None:
    """get_pr_files parses and returns the GitHub response list."""
    gh_client._installation_tokens[123] = ("cached_token", 9_999_999_999.0)

    mock_http = AsyncMock()
    mock_client_cls.return_value.__aenter__.return_value = mock_http
    mock_resp = MagicMock()
    mock_resp.json.return_value = [{"filename": "app/api/repos.py", "status": "modified"}]
    mock_http.get.return_value = mock_resp

    files = await gh_client.get_pr_files("owner", "repo", 1, 123)
    assert len(files) == 1
    assert files[0]["filename"] == "app/api/repos.py"
    mock_http.get.assert_called_once()


@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_get_file_content_returns_text(
    mock_client_cls: MagicMock, gh_client: GitHubAppClient
) -> None:
    """get_file_content fetches raw file text at the given ref."""
    gh_client._installation_tokens[123] = ("cached_token", 9_999_999_999.0)

    mock_http = AsyncMock()
    mock_client_cls.return_value.__aenter__.return_value = mock_http
    mock_resp = MagicMock()
    mock_resp.text = "def hello(): pass\n"
    mock_http.get.return_value = mock_resp

    content = await gh_client.get_file_content("owner", "repo", "app/main.py", "abc123", 123)
    assert content == "def hello(): pass\n"

    # Verify the ref param was passed
    call_kwargs = mock_http.get.call_args
    assert call_kwargs.kwargs.get("params", {}).get("ref") == "abc123"


@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_create_pr_comment_returns_comment_id(
    mock_client_cls: MagicMock, gh_client: GitHubAppClient
) -> None:
    """create_pr_comment posts to issues/comments and returns GitHub comment ID."""
    gh_client._installation_tokens[123] = ("cached_token", 9_999_999_999.0)

    mock_http = AsyncMock()
    mock_client_cls.return_value.__aenter__.return_value = mock_http
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"id": 999}
    mock_http.post.return_value = mock_resp

    comment_id = await gh_client.create_pr_comment("owner", "repo", 1, "## Docs update", 123)
    assert comment_id == 999
    mock_http.post.assert_called_once()


@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_update_pr_comment_sends_patch(
    mock_client_cls: MagicMock, gh_client: GitHubAppClient
) -> None:
    """update_pr_comment sends a PATCH request to the comment endpoint."""
    gh_client._installation_tokens[123] = ("cached_token", 9_999_999_999.0)

    mock_http = AsyncMock()
    mock_client_cls.return_value.__aenter__.return_value = mock_http
    mock_resp = MagicMock()
    mock_http.patch.return_value = mock_resp

    await gh_client.update_pr_comment("owner", "repo", 999, "updated body", 123)
    mock_http.patch.assert_called_once()

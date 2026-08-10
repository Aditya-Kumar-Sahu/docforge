"""
GitHub App client for DocForge.

Handles:
- JWT generation (RS256) for GitHub App authentication
- Installation access token exchange and caching
- PR file listing
- PR comment creation/update
"""
from __future__ import annotations

import os
import time
from typing import Any

import httpx
import structlog
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from jwt import encode as _jwt_encode  # pyjwt
from app.core.config import settings

logger = structlog.get_logger()

GITHUB_API_BASE = "https://api.github.com"


class GitHubAppClient:
    """Authenticated GitHub App API client."""

    def __init__(self) -> None:
        """Initialise the client. Reads credentials from settings."""
        self._installation_tokens: dict[int, tuple[str, float]] = {}  # {installation_id: (token, expires_at)}

    def _generate_app_jwt(self) -> str:
        """Generate a short-lived JWT for GitHub App authentication (RS256, max 10 min)."""
        now = int(time.time())
        payload = {
            "iat": now - 60,   # issued-at with 60s buffer for clock skew
            "exp": now + 9 * 60,  # 9 minutes (GitHub max is 10)
            "iss": settings.GITHUB_APP_ID,
        }
        pem_str = settings.GITHUB_APP_PRIVATE_KEY or os.environ.get("GITHUB_APP_PRIVATE_KEY", "")
        pem_data = pem_str.replace("\\n", "\n").encode()
        private_key = load_pem_private_key(pem_data, password=None)
        token: str = _jwt_encode(payload, private_key, algorithm="RS256")  # type: ignore[arg-type]
        return token

    async def _get_installation_token(self, installation_id: int) -> str:
        """Return a valid installation access token, refreshing if near expiry."""
        cached = self._installation_tokens.get(installation_id)
        if cached:
            token, expires_at = cached
            if time.time() < expires_at - 60:  # 60s buffer
                return token

        jwt_token = self._generate_app_jwt()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{GITHUB_API_BASE}/app/installations/{installation_id}/access_tokens",
                headers={
                    "Authorization": f"Bearer {jwt_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        token = str(data["token"])
        # expires_at format: "2026-08-11T00:00:00Z"
        from datetime import datetime  # noqa: PLC0415
        expires_at = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00")).timestamp()
        self._installation_tokens[installation_id] = (token, expires_at)
        logger.info("github_installation_token_refreshed", installation_id=installation_id)
        return token

    async def get_pr_files(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        installation_id: int,
    ) -> list[dict[str, Any]]:
        """Return list of changed files in a PR with filename, status, and patch."""
        token = await self._get_installation_token(installation_id)
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}/files",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
            resp.raise_for_status()
            return resp.json()  # type: ignore[no-any-return]

    async def get_file_content(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: str,
        installation_id: int,
    ) -> str:
        """Return raw file content at a specific git ref."""
        token = await self._get_installation_token(installation_id)
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}",
                params={"ref": ref},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github.raw+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
            resp.raise_for_status()
            return resp.text

    async def create_pr_comment(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        body: str,
        installation_id: int,
    ) -> int:
        """Create a new PR comment. Returns the GitHub comment ID."""
        token = await self._get_installation_token(installation_id)
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/{pr_number}/comments",
                json={"body": body},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
            resp.raise_for_status()
            return int(resp.json()["id"])

    async def update_pr_comment(
        self,
        owner: str,
        repo: str,
        comment_id: int,
        body: str,
        installation_id: int,
    ) -> None:
        """Update an existing PR comment body."""
        token = await self._get_installation_token(installation_id)
        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/comments/{comment_id}",
                json={"body": body},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
            resp.raise_for_status()


# Module-level singleton — instantiated once per worker process
github_client = GitHubAppClient()

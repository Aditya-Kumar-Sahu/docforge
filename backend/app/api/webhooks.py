"""
GitHub App webhook receiver for DocForge.

All incoming requests are verified against GITHUB_WEBHOOK_SECRET using
HMAC-SHA256. Unverified requests are rejected with 401.

Event routing:
- pull_request.opened / .synchronize  → process_pr_task (Celery)
- pull_request.closed (merged=True)   → process_pr_merged_task (Celery)
- installation.*                       → logged, no action
- Everything else                      → 200 OK (no-op)
"""
from __future__ import annotations

import hashlib
import hmac
import os
from typing import Any

import structlog
from fastapi import APIRouter, Header, HTTPException, Request, status

from app.core.config import settings

logger = structlog.get_logger()
router = APIRouter(tags=["webhooks"])


def _verify_signature(payload: bytes, signature_header: str | None) -> None:
    """Verify HMAC-SHA256 signature. Raises HTTPException(401) on failure."""
    if not signature_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Hub-Signature-256",
        )
    if not signature_header.startswith("sha256="):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature format",
        )

    secret = os.environ.get("GITHUB_WEBHOOK_SECRET") or settings.GITHUB_WEBHOOK_SECRET
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    received = signature_header.removeprefix("sha256=")

    if not hmac.compare_digest(expected, received):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )


@router.post("/webhooks/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
) -> dict[str, str]:
    """Receive and route GitHub App webhook events."""
    payload = await request.body()
    _verify_signature(payload, x_hub_signature_256)

    try:
        body: dict[str, Any] = await request.json()
    except (ValueError, UnicodeDecodeError) as exc:
        logger.warning("github_webhook_invalid_json", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    event_type = x_github_event or "unknown"
    logger.info("github_webhook_received", event_type=event_type)

    if event_type == "pull_request":
        # Extract all values first, then validate
        action: str = str(body.get("action", ""))
        installation: dict[str, Any] = body.get("installation") or {}
        installation_id: int | None = installation.get("id")
        repo_info: dict[str, Any] = body.get("repository") or {}
        pr_info: dict[str, Any] = body.get("pull_request") or {}

        full_name: str = str(repo_info.get("full_name", ""))
        github_repo_id: str = str(repo_info.get("id", ""))
        pr_number: int = int(pr_info.get("number", 0))
        head_sha: str = str((pr_info.get("head") or {}).get("sha", ""))
        merged: bool = bool(pr_info.get("merged", False))
        owner, _, repo_name = full_name.partition("/")

        if not installation_id:
            logger.warning(
                "github_webhook_missing_installation_id",
                action=action,
                repo=full_name,
            )

        if action in ("opened", "synchronize") and installation_id:
            from app.core.celery_tasks import process_pr_task  # noqa: PLC0415

            process_pr_task.delay(
                github_repo_id=github_repo_id,
                installation_id=installation_id,
                owner=owner,
                repo_name=repo_name,
                pr_number=pr_number,
                head_sha=head_sha,
            )
            logger.info("pr_task_dispatched", action=action, pr=pr_number, repo=full_name)

        elif action == "closed" and merged and installation_id:
            from app.core.celery_tasks import process_pr_merged_task  # noqa: PLC0415

            process_pr_merged_task.delay(
                github_repo_id=github_repo_id,
                installation_id=installation_id,
                owner=owner,
                repo_name=repo_name,
                pr_number=pr_number,
            )
            logger.info("pr_merged_task_dispatched", pr=pr_number, repo=full_name)

        else:
            logger.info("pr_event_ignored", action=action, merged=merged)

    elif event_type == "installation":
        action = str(body.get("action", ""))
        inst: dict[str, Any] = body.get("installation") or {}
        inst_id: int | None = inst.get("id")
        logger.info("github_installation_event", action=action, installation_id=inst_id)

    else:
        logger.debug("github_webhook_noop", event_type=event_type)

    return {"status": "ok"}

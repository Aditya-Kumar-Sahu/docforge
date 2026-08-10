"""
Tests for the GitHub App webhook endpoint.

GITHUB_WEBHOOK_SECRET is set in conftest.py before any app module is imported.
"""
import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, raise_server_exceptions=False)
WEBHOOK_SECRET = "test-webhook-secret"


def _make_signature(body: bytes) -> str:
    """Generate a valid HMAC-SHA256 signature for testing."""
    sig = hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


def _post_webhook(
    event: str,
    body: dict,  # type: ignore[type-arg]
    sig: str | None = None,
) -> object:
    """Helper to POST a signed webhook event."""
    body_bytes = json.dumps(body).encode()
    headers: dict[str, str] = {"X-GitHub-Event": event}
    headers["X-Hub-Signature-256"] = sig if sig is not None else _make_signature(body_bytes)
    return client.post("/webhooks/github", content=body_bytes, headers=headers)


def test_missing_signature_returns_401() -> None:
    """No signature header → 401."""
    response = client.post("/webhooks/github", json={"action": "opened"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing X-Hub-Signature-256"


def test_invalid_signature_returns_401() -> None:
    """Wrong signature → 401."""
    body_bytes = json.dumps({"action": "opened"}).encode()
    response = client.post(
        "/webhooks/github",
        content=body_bytes,
        headers={
            "X-Hub-Signature-256": "sha256=invalidsignature",
            "X-GitHub-Event": "pull_request",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid webhook signature"


def test_valid_ping_event_returns_200() -> None:
    """Unknown event type with valid signature → 200 no-op."""
    response = _post_webhook("ping", {"zen": "Keep it logically awesome."})
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("app.core.celery_tasks.process_pr_task.delay")
def test_pr_opened_dispatches_task(mock_delay: MagicMock) -> None:
    """pull_request opened → process_pr_task.delay called with correct args."""
    body = {
        "action": "opened",
        "installation": {"id": 123},
        "repository": {"id": 456, "full_name": "owner/repo"},
        "pull_request": {"number": 1, "head": {"sha": "abcdef"}, "merged": False},
    }
    response = _post_webhook("pull_request", body)
    assert response.status_code == 200
    mock_delay.assert_called_once_with(
        github_repo_id="456",
        installation_id=123,
        owner="owner",
        repo_name="repo",
        pr_number=1,
        head_sha="abcdef",
    )


@patch("app.core.celery_tasks.process_pr_task.delay")
def test_pr_synchronize_dispatches_task(mock_delay: MagicMock) -> None:
    """pull_request synchronize → process_pr_task.delay called."""
    body = {
        "action": "synchronize",
        "installation": {"id": 123},
        "repository": {"id": 456, "full_name": "owner/repo"},
        "pull_request": {"number": 2, "head": {"sha": "abcdef"}, "merged": False},
    }
    response = _post_webhook("pull_request", body)
    assert response.status_code == 200
    mock_delay.assert_called_once()


@patch("app.core.celery_tasks.process_pr_merged_task.delay")
@patch("app.core.celery_tasks.process_pr_task.delay")
def test_pr_closed_not_merged_no_task(
    mock_pr_delay: MagicMock, mock_merged_delay: MagicMock
) -> None:
    """pull_request closed but not merged → no task dispatched."""
    body = {
        "action": "closed",
        "installation": {"id": 123},
        "repository": {"id": 456, "full_name": "owner/repo"},
        "pull_request": {"number": 3, "head": {"sha": "abcdef"}, "merged": False},
    }
    response = _post_webhook("pull_request", body)
    assert response.status_code == 200
    mock_pr_delay.assert_not_called()
    mock_merged_delay.assert_not_called()


@patch("app.core.celery_tasks.process_pr_merged_task.delay")
def test_pr_closed_merged_dispatches_merged_task(mock_merged_delay: MagicMock) -> None:
    """pull_request closed + merged=True → process_pr_merged_task.delay called."""
    body = {
        "action": "closed",
        "installation": {"id": 123},
        "repository": {"id": 456, "full_name": "owner/repo"},
        "pull_request": {"number": 4, "head": {"sha": "abcdef"}, "merged": True},
    }
    response = _post_webhook("pull_request", body)
    assert response.status_code == 200
    mock_merged_delay.assert_called_once_with(
        github_repo_id="456",
        installation_id=123,
        owner="owner",
        repo_name="repo",
        pr_number=4,
    )


def test_installation_event_returns_200() -> None:
    """installation event → 200 OK, no crash."""
    body = {"action": "created", "installation": {"id": 123}}
    response = _post_webhook("installation", body)
    assert response.status_code == 200


def test_invalid_json_returns_400() -> None:
    """Non-JSON body with valid HMAC → 400."""
    body_bytes = b"this is not json"
    sig = _make_signature(body_bytes)
    response = client.post(
        "/webhooks/github",
        content=body_bytes,
        headers={"X-Hub-Signature-256": sig, "X-GitHub-Event": "pull_request"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid JSON payload"

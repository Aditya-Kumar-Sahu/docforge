"""
Tests for core utilities: config, analytics, chains, database session.
"""
from unittest.mock import patch


# ── Config tests ────────────────────────────────────────────────────────────

def test_settings_has_required_fields() -> None:
    from app.core.config import settings
    assert hasattr(settings, "DATABASE_URL")
    assert hasattr(settings, "REDIS_URL")
    assert hasattr(settings, "SUPABASE_JWT_SECRET")
    assert hasattr(settings, "BACKEND_CORS_ORIGINS")


def test_settings_database_url_is_postgres() -> None:
    from app.core.config import settings
    assert "postgresql" in settings.DATABASE_URL


# ── Analytics tests ────────────────────────────────────────────────────────

def test_init_analytics_disables_when_no_key() -> None:
    import posthog
    from app.core.analytics import init_analytics
    with patch("app.core.analytics.settings") as mock_settings:
        mock_settings.POSTHOG_API_KEY = None
        init_analytics()
    assert posthog.disabled is True


def test_capture_event_calls_posthog_when_enabled() -> None:
    import posthog
    posthog.disabled = False
    posthog.api_key = "phc_test"
    with patch("posthog.capture") as mock_capture:
        from app.core.analytics import capture_event
        capture_event("user-1", "test_event", {"key": "value"})
        mock_capture.assert_called_once_with(
            distinct_id="user-1",
            event="test_event",
            properties={"key": "value"},
        )


def test_capture_event_noop_when_disabled() -> None:
    import posthog
    posthog.disabled = True
    with patch("posthog.capture") as mock_capture:
        from app.core.analytics import capture_event
        capture_event("user-1", "test_event")
        mock_capture.assert_not_called()


# ── Chains stub tests ──────────────────────────────────────────────────────

def test_extract_schema_chain_returns_dict() -> None:
    from app.core.chains import extract_schema_chain
    result = extract_schema_chain("class User(BaseModel): name: str")
    assert isinstance(result, dict)


def test_generate_endpoint_docs_chain_returns_dict() -> None:
    from app.core.chains import generate_endpoint_docs_chain
    result = generate_endpoint_docs_chain({"method": "GET", "path": "/users"})
    assert isinstance(result, dict)
    assert "description" in result


def test_review_docs_chain_returns_status() -> None:
    from app.core.chains import review_docs_chain
    result = review_docs_chain({"description": "Gets all users"})
    assert isinstance(result, dict)
    assert "status" in result


def test_generate_markdown_docs_chain_returns_string() -> None:
    from app.core.chains import generate_markdown_docs_chain
    result = generate_markdown_docs_chain({"openapi": "3.1.0"})
    assert isinstance(result, str)
    assert len(result) > 0


# ── Logger tests ───────────────────────────────────────────────────────────

def test_configure_logging_runs_without_error() -> None:
    from app.core.logger import configure_logging
    configure_logging()  # Should not raise


# ── Database tests ────────────────────────────────────────────────────────

def test_get_db_is_async_generator() -> None:
    import inspect
    from app.core.database import get_db
    assert inspect.isasyncgenfunction(get_db)

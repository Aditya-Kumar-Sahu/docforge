"""
Pytest configuration for the DocForge backend test suite.

Sets environment variables BEFORE any app module is imported, so that
Settings() reads the test values. This avoids needing a real .env file in CI.
"""
import os

# ── Test environment defaults ──────────────────────────────────────────────
# These must be set before `app.core.config` is imported by any test module.
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-secret-key-that-is-long-enough")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://docforge:docforge_password@127.0.0.1:5432/docforge_db",
)
os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:6379/0")
os.environ.setdefault("POSTHOG_API_KEY", "phc_test")
os.environ.setdefault("GITHUB_WEBHOOK_SECRET", "test-webhook-secret")
os.environ.setdefault("GITHUB_APP_ID", "12345")
os.environ.setdefault("GITHUB_APP_PRIVATE_KEY", "")  # overridden per-test where needed

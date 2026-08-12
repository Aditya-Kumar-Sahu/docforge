import posthog
from app.core.config import settings

from typing import Any

def init_analytics() -> None:
    if settings.POSTHOG_API_KEY:
        posthog.api_key = settings.POSTHOG_API_KEY
        posthog.host = settings.POSTHOG_HOST
    else:
        posthog.disabled = True

def capture_event(user_id: str, event_name: str, properties: dict[str, Any] | None = None) -> None:
    """
    Captures an event to PostHog safely.
    """
    if posthog.disabled or not settings.POSTHOG_API_KEY:
        return
    if not getattr(posthog, "api_key", None):
        init_analytics()
    if posthog.disabled or not posthog.api_key:
        return
    try:
        posthog.capture(distinct_id=user_id, event=event_name, properties=properties or {})
    except Exception:  # noqa: BLE001
        pass

import posthog
from app.core.config import settings

from typing import Any

def init_analytics() -> None:
    if settings.POSTHOG_API_KEY:
        posthog.api_key = settings.POSTHOG_API_KEY
        posthog.host = settings.POSTHOG_HOST
        # Disabled for local development if needed, but usually kept on for backend
        # posthog.disabled = True 
    else:
        posthog.disabled = True

def capture_event(user_id: str, event_name: str, properties: dict[str, Any] | None = None) -> None:
    """
    Captures an event to PostHog.
    """
    if posthog.disabled:
        return
    posthog.capture(distinct_id=user_id, event=event_name, properties=properties or {})

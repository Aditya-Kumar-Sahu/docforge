"""
Sliding window rate limiter for DocForge.
Supports in-memory and Redis-backed rate limiting per user/IP.
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Dict, List, Tuple
from fastapi import HTTPException, Request


class RateLimiter:
    """In-memory sliding window rate limiter."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 3600) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # key -> list of timestamps
        self.requests: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> Tuple[bool, int]:
        """
        Check if request is allowed for `key`.
        Returns (is_allowed, seconds_to_wait).
        """
        now = time.time()
        window_start = now - self.window_seconds

        # Prune old timestamps
        timestamps = [t for t in self.requests[key] if t > window_start]
        self.requests[key] = timestamps

        if len(timestamps) < self.max_requests:
            self.requests[key].append(now)
            return True, 0
        else:
            oldest = timestamps[0]
            retry_after = int(self.window_seconds - (now - oldest)) + 1
            return False, max(1, retry_after)


# Global rate limiter instances for specific route groups
scan_rate_limiter = RateLimiter(max_requests=10, window_seconds=3600)  # 10 scans / hour
api_rate_limiter = RateLimiter(max_requests=100, window_seconds=60)    # 100 requests / minute


def check_rate_limit(request: Request, limiter: RateLimiter = api_rate_limiter) -> None:
    """FastAPI dependency to enforce rate limits."""
    user_id: str | None = getattr(request.state, "user_id", None)
    client_ip = request.client.host if request.client else "127.0.0.1"
    key = user_id if user_id else client_ip

    allowed, retry_after = limiter.is_allowed(key)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )

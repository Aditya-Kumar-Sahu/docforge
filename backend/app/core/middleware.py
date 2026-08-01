import time
import uuid
import structlog
import jwt
from typing import Callable, Awaitable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings

logger = structlog.get_logger()

# Routes that do NOT require authentication
PUBLIC_PATHS = {"/health", "/sentry-debug", "/monitoring"}


class CoreMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        start_time = time.time()
        request_id = str(uuid.uuid4())

        # Check JWT for protected routes (e.g., /api/)
        user_id: str | None = None
        if request.url.path.startswith("/api/") and request.url.path not in PUBLIC_PATHS:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Missing or invalid authorization header"},
                )

            token = auth_header.split(" ", 1)[1]
            try:
                payload = jwt.decode(
                    token,
                    settings.SUPABASE_JWT_SECRET,
                    algorithms=["HS256"],
                    audience="authenticated",
                )
                user_id = payload.get("sub")
            except jwt.ExpiredSignatureError:
                return JSONResponse(status_code=401, content={"detail": "Token has expired"})
            except jwt.InvalidTokenError:
                return JSONResponse(status_code=401, content={"detail": "Invalid token"})
            except Exception:  # noqa: BLE001
                return JSONResponse(status_code=401, content={"detail": "Authentication failed"})

        # Attach user_id to request state so route handlers can access it
        request.state.user_id = user_id

        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            user_id=user_id,
            endpoint=request.url.path,
            method=request.method,
        )

        response = await call_next(request)

        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            "request_completed",
            duration_ms=round(duration_ms, 2),
            status_code=response.status_code,
        )
        return response

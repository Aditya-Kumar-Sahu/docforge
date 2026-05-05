import time
import uuid
from typing import Awaitable, Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger()

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, 
        request: Request, 
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        
        start_time = time.time()
        
        response = await call_next(request)
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        user_id = "anonymous"
        if hasattr(request.state, "user"):
            user_id = getattr(request.state.user, "id", "anonymous")
            
        logger.info(
            "request_finished",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            user_id=user_id
        )
        
        response.headers["X-Request-ID"] = request_id
        return response

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

class CoreMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        # Check JWT for protected routes (e.g., /api/)
        user_id = None
        if request.url.path.startswith("/api/"):
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return JSONResponse(status_code=401, content={"detail": "Missing or invalid token"})
            
            token = auth_header.split(" ")[1]
            try:
                # Assuming Supabase JWT
                payload = jwt.decode(token, settings.SUPABASE_JWT_SECRET, algorithms=["HS256"], audience="authenticated")
                user_id = payload.get("sub")
            except Exception as e:
                return JSONResponse(status_code=401, content={"detail": "Invalid token", "error": str(e)})

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
            status_code=response.status_code
        )
        return response

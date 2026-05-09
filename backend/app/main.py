from typing import Any
from fastapi import FastAPI, Depends
from app.core.config import settings
from app.core.auth import get_current_user
from app.models.models import User
from app.core.logging import LoggingMiddleware
from app.api import repos
import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG
)

app.add_middleware(LoggingMiddleware)

app.include_router(repos.router, prefix="/api")

@app.get("/health")
async def health_check() -> dict[str, str]:
    logger.info("health_check_triggered")
    return {"status": "healthy", "version": "0.1.0"}

@app.get("/me")
async def get_me(user: User = Depends(get_current_user)) -> dict[str, str]:
    return {"id": user.id, "email": user.email}

@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Welcome to DocForge API"}

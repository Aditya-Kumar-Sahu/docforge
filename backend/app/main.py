import structlog
import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.logger import configure_logging
from app.core.middleware import CoreMiddleware
from app.core.config import settings
from app.core.analytics import init_analytics

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
        send_default_pii=True,
    )

configure_logging()
init_analytics()
logger = structlog.get_logger()

app = FastAPI(title="DocForge API", version="0.1.0")

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.add_middleware(CoreMiddleware)

@app.get("/health")
async def health_check() -> dict[str, str]:
    logger.info("health_check_requested", endpoint="/health")
    return {"status": "ok"}

@app.get("/sentry-debug")
async def trigger_error() -> None:
    division_by_zero = 1 / 0
    del division_by_zero


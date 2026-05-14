import structlog
from fastapi import FastAPI
from app.core.logger import configure_logging
from app.core.middleware import CoreMiddleware

configure_logging()
logger = structlog.get_logger()

app = FastAPI(title="DocForge API", version="0.1.0")
app.add_middleware(CoreMiddleware)

@app.get("/health")
async def health_check():
    logger.info("health_check_requested", endpoint="/health")
    return {"status": "ok"}


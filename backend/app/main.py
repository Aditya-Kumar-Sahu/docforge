from fastapi import FastAPI, Depends
from app.core.config import settings
from app.core.auth import get_current_user
from app.models.models import User
import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG
)

@app.get("/health")
async def health_check():
    logger.info("health_check_triggered")
    return {"status": "healthy", "version": "0.1.0"}

@app.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email}

@app.get("/")
async def root():
    return {"message": "Welcome to DocForge API"}

from fastapi import FastAPI, Depends
from pydantic_settings import BaseSettings
import structlog

class Settings(BaseSettings):
    app_name: str = "DocForge API"
    debug: bool = False
    database_url: str = "postgresql+asyncpg://postgres:password@db:5432/docforge"
    supabase_url: str = ""
    supabase_key: str = ""

    class Config:
        env_file = ".env"

settings = Settings()

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

app = FastAPI(title=settings.app_name)

@app.get("/health")
async def health_check():
    logger.info("health_check_triggered")
    return {"status": "healthy", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

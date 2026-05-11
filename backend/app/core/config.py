
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "DocForge API"
    DEBUG: bool = False
    DEBUG_AUTH: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@db:5432/docforge"
    
    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    
    # AI
    GEMINI_API_KEY: str | None = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

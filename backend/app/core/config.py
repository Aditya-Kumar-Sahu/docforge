from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://docforge:docforge_password@127.0.0.1:5432/docforge_db"
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    SECRET_KEY: str = "change-this-in-production"
    ALGORITHM: str = "HS256"
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""
    SENTRY_DSN: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

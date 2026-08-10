from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://docforge:docforge_password@127.0.0.1:5432/docforge_db"
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    SECRET_KEY: str = "change-this-in-production"
    ALGORITHM: str = "HS256"
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    SENTRY_DSN: str | None = None
    POSTHOG_API_KEY: str | None = None
    POSTHOG_HOST: str = "https://us.i.posthog.com"
    GEMINI_API_KEY: str = ""
    LITELLM_MODEL: str = "gemini/gemini-2.0-flash"
    LANGSMITH_API_KEY: str | None = None
    LANGSMITH_TRACING: bool = False
    
    GITHUB_APP_ID: str = ""
    GITHUB_APP_PRIVATE_KEY: str = ""  # PEM content, newlines as \\n in env
    GITHUB_WEBHOOK_SECRET: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

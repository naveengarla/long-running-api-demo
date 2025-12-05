from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Long Running API Demo"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5433/app"
    SYNC_DATABASE_URL: str = "postgresql+psycopg2://user:password@localhost:5433/app"

    class Config:
        case_sensitive = True

settings = Settings()

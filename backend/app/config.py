from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://expense_user:expense_pass@localhost:5432/expense_tracker"
    APP_ENV: str = "development"
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,https://mayank06711.xyz"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

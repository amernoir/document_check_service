from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/doccheck"
    UPLOAD_DIR: str = "./uploads"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    JWT_SECRET: str = "change-me-in-production"
    JWT_EXPIRE_HOURS: int = 24

    model_config = {"env_file": ".env"}


settings = Settings()

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/doccheck"
    UPLOAD_DIR: str = "./uploads"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    JWT_SECRET: str = ""
    JWT_EXPIRE_MINUTES: int = 30

    model_config = {"env_file": ".env"}


settings = Settings()

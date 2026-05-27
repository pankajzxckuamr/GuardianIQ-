from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "GuardianIQ"

    DATABASE_URL: str

    SECRET_KEY: str

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    ALGORITHM: str = "HS256"

    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    class Config:
        env_file = ".env"


settings = Settings()

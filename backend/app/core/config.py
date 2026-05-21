from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "GuardianIQ"

    DATABASE_URL: str

    SECRET_KEY: str = "32d425c6255010ae7514096441a3d590a9def39add4c9e41a84714be3db57078"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"


settings = Settings()

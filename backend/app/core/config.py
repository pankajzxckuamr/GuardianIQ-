from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "GuardianIQ"

    DATABASE_URL: str

    SECRET_KEY: str

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    ALGORITHM: str = "HS256"

    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Phase 2 Scheduler configurations
    SCHEDULER_ENABLED: bool = False
    PHASE2_SCHEDULER_ENABLED: bool = False
    SCHEDULER_POLL_INTERVAL_SECONDS: int = 60
    SCHEDULER_MAX_SCHEDULES_PER_CYCLE: int = 25
    SCHEDULER_WORKER_ID: str = "worker-node-1"
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "JSON"

    class Config:
        env_file = ".env"


settings = Settings()

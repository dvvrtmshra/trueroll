from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "sqlite:///./trueroll.db"
    TAMPER_DATABASE_URL: str = ""

    DEMO_MODE: bool = True

    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_EXPIRE_DAYS: int = 7

    HMAC_KEY: str = "change-me-hmac"

    ANOMALY_ENABLED: bool = False

    FRONTEND_ORIGIN: str = "http://localhost:5173"

    VAULT_DIR: str = "./vault"


settings = Settings()

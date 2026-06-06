from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv(".env")


class Settings(BaseSettings):
    ACCESS_TOKEN_EXPIRY_TIME: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    LOG_DIR: str
    AVATAR_SEEDS: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from logger_config import app_logger


class Settings(BaseSettings):
    BOT_TOKEN: str
    EXP_FOR_IMPROVIZATION_TASKS: int
    SPEECHY_SALT: str
    REFERRAL_CODE_LENGTH: int

    # Делаем поля БД необязательными, если есть DATABASE_URL
    DB_HOST: Optional[str] = None
    DB_PORT: Optional[str] = None
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_NAME: Optional[str] = None
    DATABASE_URL: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra='ignore'  # Игнорировать лишние переменные
    )

    def get_database_url(self) -> str:
        # Приоритет у DATABASE_URL
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if "postgresql://" in url and "+asyncpg" not in url:
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url

        # Ручная сборка
        if all([self.DB_HOST, self.DB_USER, self.DB_PASSWORD, self.DB_NAME]):
            port = self.DB_PORT or "5432"
            return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{port}/{self.DB_NAME}"

        raise ValueError("Neither DATABASE_URL nor DB_* credentials are set")

    def get_bot_token(self) -> str:
        return self.BOT_TOKEN

    def get_EXP_FOR_IMPROVIZATION_TASKS(self) -> int:
        return self.EXP_FOR_IMPROVIZATION_TASKS

    def get_SPEECHY_SALT(self) -> str:
        return self.SPEECHY_SALT

    def get_REFERRAL_CODE_LENGTH(self) -> int:
        return self.REFERRAL_CODE_LENGTH


settings = Settings()
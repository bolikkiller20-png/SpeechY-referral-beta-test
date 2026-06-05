import os
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

from logger_config import app_logger


class Settings(BaseSettings):
    BOT_TOKEN: str
    DB_HOST: str
    DB_PORT: str
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    EXP_FOR_IMPROVIZATION_TASKS: int
    DATABASE_URL: Optional[str] = None
    SPEECHY_SALT: str
    REFERRAL_CODE_LENGTH: int

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        app_logger.info("Загрузка конфигурации Settings")
        app_logger.debug(f"Подключение к БД: {self.DB_USER}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}")

    def get_database_url(self) -> str:
        # ✅ Если есть DATABASE_URL - используем
        if self.DATABASE_URL:
            # Преобразуем для asyncpg
            url = self.DATABASE_URL
            if "postgresql://" in url and "+asyncpg" not in url:
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url

        # ✅ Если нет DATABASE_URL, собираем из частей
        if self.DB_HOST and self.DB_USER and self.DB_PASSWORD and self.DB_NAME:
            port = self.DB_PORT or 5432
            return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{port}/{self.DB_NAME}"

    def get_bot_token(self):
        return self.BOT_TOKEN

    def get_EXP_FOR_IMPROVIZATION_TASKS(self):
        return self.EXP_FOR_IMPROVIZATION_TASKS

    def get_SPEECHY_SALT(self) -> str:
        return self.SPEECHY_SALT


    def get_REFERRAL_CODE_LENGTH(self) -> int:
        return self.REFERRAL_CODE_LENGTH



settings = Settings()

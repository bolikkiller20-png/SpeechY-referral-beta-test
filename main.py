import asyncio
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from database import db
from database.services.notification_restore import restore_all_notifications
from middlewares.anchor import AnchorManagerMiddleware
from middlewares.db import DbSessionMiddleware
from routers import routers
from logger_config import app_logger
from services.Scheduler import message_scheduler

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def ensure_tables_exist():
    """Временно: создает таблицы если их нет (костыль для Railway)"""
    from sqlalchemy.ext.asyncio import create_async_engine
    from database.base import Base
    from config import settings

    try:
        engine = create_async_engine(settings.get_database_url())
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()
        app_logger.info("✅ Таблицы проверены/созданы")
    except Exception as e:
        app_logger.error(f"Ошибка при проверке таблиц: {e}")


async def update_seed_data():
    """Заполняет базу данных начальными данными (курсы, задания, промокоды)"""
    from database.session import get_async_session
    from database.seed import DataSeeder

    try:
        async for session in get_async_session():
            seeder = DataSeeder(session)
            await seeder.update_seed_data()
            app_logger.info("✅ Начальные данные успешно загружены")
            break
    except Exception as e:
        app_logger.error(f"❌ Ошибка при загрузке начальных данных: {e}")
        raise


def run_migrations():
    """Запускает миграции Alembic перед стартом бота."""
    try:
        from alembic.config import Config
        from alembic import command
        from config import settings

        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", settings.get_database_url())

        # Принудительно ставим метку head, чтобы избежать проблем
        command.stamp(alembic_cfg, "head")

        # Применяем миграции
        command.upgrade(alembic_cfg, "head")
        app_logger.info("✅ Миграции успешно применены")
    except Exception as e:
        app_logger.error(f"❌ Ошибка выполнения миграций: {e}")
        raise


async def on_startup():
    """Запускается при старте бота."""
    app_logger.info("Бот запущен")


async def on_shutdown():
    """Запускается при остановке бота."""
    app_logger.info("Закрытие соединений с БД...")
    message_scheduler.stop()
    await db.close()
    app_logger.info("Бот остановлен")


async def main():
    app_logger.info("Инициализация бота...")

    # 1. Создаем таблицы если их нет
    await ensure_tables_exist()

    # 2. Запускаем миграции
    run_migrations()

    # 3. Заполняем начальными данными (курсы, задания, промокоды)
    await update_seed_data()

    # 4. Запускаем планировщик
    message_scheduler.start()

    BOT_TOKEN = settings.get_bot_token()
    bot = Bot(
        BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            link_preview_is_disabled=True
        )
    )

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp["bot"] = bot

    dp.update.middleware(DbSessionMiddleware())
    dp.update.middleware(AnchorManagerMiddleware())
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.include_routers(*routers)

    try:
        # 5. Восстанавливаем уведомления
        async with await db.get_session() as session:
            from database.repositories.NotificationRepository import NotificationRepository
            notification_repo = NotificationRepository(session)
            await restore_all_notifications(bot, notification_repo)

        # 6. Запускаем поллинг
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        app_logger.info("Бот остановлен принудительно")
        sys.exit(0)
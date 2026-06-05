from aiogram import BaseMiddleware

from database import db
from database.repositories.CompletedTaskRepository import CompletedTaskRepository
from database.repositories.ConditionRepository import ConditionRepository
from database.repositories.CourseRepository import CourseRepository
from database.repositories.NotificationRepository import NotificationRepository
from database.repositories.ProgressRepository import ProgressRepository
from database.repositories.PromoCodeRepository import PromoCodeRepository
from database.repositories.PromoCodeUsageRepository import PromoCodeUsageRepository
from database.repositories.ReferralRepository import ReferralRepository
from database.repositories.TaskRepository import TaskRepository
from database.repositories.UserRepository import UserRepository


class DbSessionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):

        async with db.session_maker() as session:
            data["session"] = session
            data["user_repo"] = UserRepository(session)
            data["notification_repo"] = NotificationRepository(session)
            data["course_repo"] = CourseRepository(session)
            data["progress_repo"] = ProgressRepository(session)
            data["task_repo"] = TaskRepository(session)
            data["condition_repo"] = ConditionRepository(session)
            data["completed_task_repo"] = CompletedTaskRepository(session)
            data["promo_code_repo"] = PromoCodeRepository(session)
            data["referral_repo"] = ReferralRepository(session)
            data["promo_code_usage_repo"] = PromoCodeUsageRepository(session)
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise

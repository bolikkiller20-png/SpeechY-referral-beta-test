from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from schemas.schemas import StreakStatus
from utils.ReferralUtils import ReferralUtils


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def update_trials_amount(
            self,
            user_id: int,
            delta: int
    ) -> int:
        res = await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(trial_amount=User.trial_amount + delta)
        )
        return res.rowcount

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """
        Get user by their Telegram ID.

        :param telegram_id: User's Telegram ID
        :return: User object
        :raises ValueError: If user with given telegram_id is not found
        """
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return None
        return user

    async def get_by_id(
            self,
            id: int
    ) -> Optional[User]:
        res = await self.session.execute(
            select(User).where(User.id == id)
        )
        user = res.scalar_one_or_none()
        if not user:
            raise ValueError("Пользователь не найден")
        return user

    async def create(self, **kwargs) -> User:
        """
        Add User object in db by dictionary of params
        :param kwargs:
        :return:
        User object
        """
        user = User(**kwargs)
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_or_create(
            self,
            telegram_id: int,
            **defaults
    ) -> tuple[User, bool]:
        """
        Get user by his telegram id or create user if user not in db
        :param telegram_id:
        :param defaults:
        :return:
        User object and success status by tuple
        """
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            return user, False
        return await self.create(telegram_id=telegram_id, **defaults), True

    async def toggle_user_notifications(self, telegram_id: int) -> bool:
        """
        Turn on or Turn off user notifications
        :param telegram_id:
        :return:
        success status
        """
        user = await self.get_by_telegram_id(telegram_id)
        if not user.notifications:
            user.notifications = True

            return True
        user.notifications = False
        return False

    async def change_name_by_telegram_id(
            self,
            telegram_id: int,
            new_name: str
    ) -> bool:
        """
        Change username by his telegram id
        :param telegram_id:
        :param new_name:
        :return:
        success status
        """
        user = await self.get_by_telegram_id(telegram_id)
        if not user:
            return False
        user.name = new_name
        return True

    async def update_user_amount_of_days_series(
            self,
            telegram_id: int,
    ) -> tuple[int, StreakStatus]:

        user = await self.get_by_telegram_id(telegram_id)
        if not user:
            raise ValueError("Ты не зарегистрирован в боте\n"
                             "Используй /start, чтобы зарегистрироваться")
        today = date.today()
        last_date = user.last_task_completed_date

        if last_date == today:
            return user.series_of_days_amount, StreakStatus.ALREADY_COMPLETED

        if last_date == today - timedelta(days=1):
            user.series_of_days_amount += 1
            user.last_task_completed_date = today
            await self.session.commit()
            return user.series_of_days_amount, StreakStatus.INCREASED

        if last_date is None:
            user.series_of_days_amount = 1
            user.last_task_completed_date = today
            await self.session.commit()
            return 1, StreakStatus.FIRST_TASK

        days_missed = (today - last_date).days
        user.series_of_days_amount = 1
        user.last_task_completed_date = today
        await self.session.commit()

        if days_missed == 1:
            return 1, StreakStatus.RESET
        else:
            return 1, StreakStatus.STREAK_BROKEN

    async def get_all_users_with_enabled_notifications(self) -> List[User]:
        result = await self.session.execute(
            select(User).where(User.notifications == True)
        )
        return result.scalars().all()

    async def update_user_pro_discount(
            self,
            user_id: int,
            new_discount: int
    ) -> int:
        user = await self.get_by_id(user_id)
        if user.pro_discount is None:
            user.pro_discount = 0
        if user.pro_discount < new_discount:
            res = await self.session.execute(
                update(User)
                .where(User.id == user_id)
                .values(pro_discount=new_discount)
            )
            return res.rowcount
        else:
            return 0


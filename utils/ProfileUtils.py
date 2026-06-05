from aiogram.types import Message, CallbackQuery

from database.repositories.CourseRepository import CourseRepository
from database.repositories.NotificationRepository import NotificationRepository
from database.repositories.ProgressRepository import ProgressRepository
from database.repositories.UserRepository import UserRepository


class ProfileUtils:
    @staticmethod
    async def get_profile_text(
            event,  # Message или CallbackQuery
            user_repo: UserRepository,
            notification_repo: NotificationRepository,
            progress_repo: ProgressRepository,
            course_repo: CourseRepository,
            custom_notifications_msg: str = None,
    ):
        # --- Унификация источников ---
        if isinstance(event, Message):
            user_id = event.from_user.id
            send = event.answer
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            send = event.message.answer
        else:
            raise TypeError("show_profile принимает только Message или CallbackQuery")

        user = await user_repo.get_by_telegram_id(user_id)
        print(user.id)
        if not user:
            return await send("Пользователь не найден")
        courses_progress = await progress_repo.get_user_progress(user.id)
        i = 1
        courses_progress_text = ""
        for course_progress in courses_progress:
            course = await course_repo.get_course_by_id(course_progress.course_id)
            courses_progress_text += f"{i}. <b>{course.name}</b>  <i>{course_progress.progress}</i> XP" \
                                     f"   Уровень: <i>{course_progress.level}</i>\n"
            i += 1
        if custom_notifications_msg is not None:
            notifications_display = custom_notifications_msg
        else:
            notifications = await notification_repo.get_all_raw(user.id)
            if notifications:
                times_str = " ".join(t.strftime("%H:%M") for t in notifications)
                notifications_display = f"(<i>{times_str}</i>)"
            else:
                notifications_display = "(выключены)"

        text = "📊 <b><i>Твой профиль</i></b>\n\n" \
            f"👤 Имя: <b>{user.name}</b>\n"\
            f"🔥 Серия: <b>{user.series_of_days_amount} дней</b>\n"\
            f"🔔 Уведомления: {'✅ <b>Вкл</b>' if user.notifications else '❌ <b>Выкл</b>'} {notifications_display}\n\n" \
               f"⭐️ Количество попыток Pro-версии: <b>{user.trial_amount}</b>\n"\
            f"\n📚 <b><i>Твой прогресс:</i></b>\n"\
            f"{courses_progress_text}"\
            f""
        return text




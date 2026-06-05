from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from Managers.AnchorMessageManager import AnchorMessageManager
from database.repositories.CourseRepository import CourseRepository
from database.repositories.NotificationRepository import NotificationRepository
from database.repositories.ProgressRepository import ProgressRepository
from database.repositories.UserRepository import UserRepository
from keyboards.ProfileKeyboards import profile_keyboard
from keyboards.RegisterKeyboards import get_skip_notifications_keyboard
from logger_config import app_logger
from services.Scheduler import message_scheduler
from states.UserStates import UserStates
from utils.ProfileUtils import ProfileUtils
from utils.UserUtils import UserUtils

register_router = Router()


@register_router.message(Command("start"))
async def name_handler(
        message: Message,
        state: FSMContext,
        session: AsyncSession,
        user_repo: UserRepository,
        notification_repo: NotificationRepository,
        course_repo: CourseRepository,
        progress_repo: ProgressRepository
):
    user = await user_repo.get_by_telegram_id(message.from_user.id)
    if not user:
        new_user, created = await user_repo.get_or_create(
            telegram_id=message.from_user.id,
            name="",
            username=message.from_user.username or "",
            is_admin=False,
            series_of_days_amount=0,
            notifications=False
        )
        anchor_msg_manager = AnchorMessageManager(
            user_id=new_user.id,
            session=session,
            chat_id=message.chat.id,
            bot=message.bot,
            state=state
        )
        await anchor_msg_manager.delete_user_message(message)
        sent = await anchor_msg_manager.send_anchor(
            "Привет!\n"
            "Меня зовут SpeechY. Я стану твоим проводником в мир <b>уверенной</b> и <i>красивой</i> речи\n"
            "Давай знакомиться. <i><u>Как тебя зовут?</u></i>"
        )
        await anchor_msg_manager.save_anchor(sent.message_id)
        await state.set_state(UserStates.name)

    if user:
        anchor_msg_manager = AnchorMessageManager(
            user_id=user.id,
            session=session,
            chat_id=message.chat.id,
            bot=message.bot,
            state=state
        )
        await anchor_msg_manager.delete_user_message(message)
        print("Сработало условие")
        text = await ProfileUtils.get_profile_text(
            message, user_repo, notification_repo, progress_repo, course_repo
        )
        await anchor_msg_manager.send_anchor(
            text=text,
            reply_markup=profile_keyboard().as_markup()
        )
        return

    await state.set_state(UserStates.name)


@register_router.message(UserStates.name)
async def profile_handler(
        message: Message,
        state: FSMContext,
        user_repo: UserRepository,
        course_repo: CourseRepository,
        progress_repo: ProgressRepository,
        anchor_manager: AnchorMessageManager
):

    try:
        UserUtils.validate_user_name(message.text)
    except ValueError as e:
        error_string_proto = str(e) + "\nДавай попробуем еще раз"
        await anchor_manager.delete_user_message(message)

        await anchor_manager.edit_anchor(error_string_proto)
        await state.set_state(UserStates.name)
        return

    await user_repo.change_name_by_telegram_id(message.from_user.id, message.text)

    available_courses = await course_repo.get_all_available_courses()
    for course in available_courses:
        await progress_repo.add_progress_to_user(message.from_user.id, course.id)
    keyboard = get_skip_notifications_keyboard()
    await anchor_manager.edit_anchor(
        f"Рад знакомству {message.text} !\n"
        f"Теперь напиши мне, когда тебе <i>напоминать</i> о тренировках\n"
        f"Например, 9:30 10:30 11:30",
        reply_markup=keyboard.as_markup()
    )
    await anchor_manager.delete_user_message(message)
    await state.set_state(UserStates.notifications)


@register_router.message(UserStates.notifications)
async def customization_notifications_handler(
        message: Message,
        state: FSMContext,
        notification_repo: NotificationRepository,
        user_repo: UserRepository,
        course_repo: CourseRepository,
        progress_repo: ProgressRepository,
        session: AsyncSession
):
    user = await user_repo.get_by_telegram_id(message.from_user.id)
    anchor_msg_manager = AnchorMessageManager(
        user_id=user.id,
        session=session,
        chat_id=message.chat.id,
        bot=message.bot,
        state=state
    )
    try:

        notifications_times = UserUtils.validate_user_notifications(message.text)
        app_logger.info(f"Получены времена уведомлений: {notifications_times}")

        if notifications_times:
            message_scheduler.remove_all_user_notifications(message.from_user.id)
            await notification_repo.clear_all_user_notifications(user.id)
            for time in notifications_times:
                notification = await notification_repo.add_notification_from_string(message.from_user.id, time)
                app_logger.info(f"Уведомление в БД: id={notification.id if notification else None}")
                if notification:
                    hour, minute = map(int, time.split(':'))
                    app_logger.info(f"Планируем уведомление для {message.from_user.id} на {hour}:{minute}")
                    message_scheduler.scheduler_daily_notification(
                        bot=message.bot,
                        telegram_id=message.from_user.id,
                        hour=hour,
                        minute=minute,
                        notification_id=notification.id,
                        anchor_manager=anchor_msg_manager
                    )
                    app_logger.info(f"Уведомление запланировано")

        await user_repo.toggle_user_notifications(message.from_user.id)
        profile_text = await ProfileUtils.get_profile_text(message, user_repo, notification_repo, progress_repo, course_repo)
        await anchor_msg_manager.edit_anchor(profile_text, reply_markup=profile_keyboard().as_markup())
        await anchor_msg_manager.delete_user_message(message)
        await state.set_state(None)
    except ValueError as e:
        await anchor_msg_manager.edit_anchor(str(e), reply_markup=get_skip_notifications_keyboard().as_markup())
        await anchor_msg_manager.delete_user_message(message)



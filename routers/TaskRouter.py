from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from Managers.AnchorMessageManager import AnchorMessageManager
from database.repositories.CompletedTaskRepository import CompletedTaskRepository
from database.repositories.ConditionRepository import ConditionRepository
from database.repositories.CourseRepository import CourseRepository
from database.repositories.ProgressRepository import ProgressRepository
from database.repositories.TaskRepository import TaskRepository
from database.repositories.UserRepository import UserRepository
from keyboards.TaskKeyboards import retry_voice_message_keyboard, task_menu_keyboard, course_task_menu_keyboard, \
    confirm_retell_keyboard
from logger_config import app_logger
from schemas.schemas import CourseName, StreakStatus, ImprovizationTaskName, DictionTaskName
from services.TaskService import task_handler_factory
from states.TaskStates import TaskStates
from utils.TaskUtils import TaskUtils

task_router = Router()


@task_router.callback_query(F.data == "complete_tasks")
async def complete_tasks_handler(
        callback: CallbackQuery,
        course_repo: CourseRepository,
        anchor_manager: AnchorMessageManager,
        bot: Bot
):
    await anchor_manager.delete_all_notification_messages(bot, callback.message.chat.id)
    msg = await TaskUtils.get_all_available_tasks_message(course_repo)
    await anchor_manager.edit_anchor(
        msg,
        reply_markup=task_menu_keyboard().as_markup()
    )


@task_router.callback_query(F.data == "task_improvisation")
async def task_improvisation_handler(
        callback: CallbackQuery,
        task_repo: TaskRepository,
        condition_repo: ConditionRepository,
        progress_repo: ProgressRepository,
        user_repo: UserRepository,
        state: FSMContext,
        anchor_manager: AnchorMessageManager
):
    app_logger.debug("Пришли в импровизацию")
    await task_handler_factory(
        callback=callback,
        task_repo=task_repo,
        condition_repo=condition_repo,
        progress_repo=progress_repo,
        user_repo=user_repo,
        state=state,
        anchor_manager=anchor_manager,
        course_name=CourseName.IMPROVISATION
    )


@task_router.callback_query(F.data == "task_diction")
async def task_diction_handler(
        callback: CallbackQuery,
        task_repo: TaskRepository,
        condition_repo: ConditionRepository,
        progress_repo: ProgressRepository,
        user_repo: UserRepository,
        state: FSMContext,
        anchor_manager: AnchorMessageManager
):
    app_logger.debug("Зашли в дикцию")

    await task_handler_factory(
        callback=callback,
        task_repo=task_repo,
        condition_repo=condition_repo,
        progress_repo=progress_repo,
        user_repo=user_repo,
        state=state,
        anchor_manager=anchor_manager,
        course_name=CourseName.DICTION
    )


@task_router.message(TaskStates.voice_message, lambda msg: msg.voice)
async def handle_voice(
        message: Message,
        state: FSMContext,
        anchor_manager: AnchorMessageManager
):
    app_logger.info(
        "Зашли в хендлер обработки голосовго сообщения"
    )
    print("Зашли в хендлер обработки голосовго сообщения")
    duration = message.voice.duration
    print("duration", duration)
    data = await state.get_data()
    task_name = data.get('task_name')
    begin_duration = 60
    end_duration = 180
    if task_name == DictionTaskName.TONGUE_TWISTER:
        begin_duration = 10
        end_duration = 90
    elif task_name == DictionTaskName.VOWELS_AND_CONSONANTS:
        begin_duration = 30
    if begin_duration <= duration <= end_duration:

        await anchor_manager.send_anchor(
            f"Голосовое получил!\nСохраняем его?",
            reply_markup=retry_voice_message_keyboard().as_markup()
        )
        await anchor_manager.delete_all_temp_messages()
        await anchor_manager.add_temp_message(message)
        await state.set_state(None)

    else:
        data = await state.get_data()
        msg = await message.answer(
            f"Голосовое слишком короткое, тебе надо говорить минимум 60 секунд\n"
        )
        await anchor_manager.add_temp_message(msg)
        if data.get("task_name") == ImprovizationTaskName.RETELL:
            await anchor_manager.send_anchor(
                data.get("formatted_message"),
                reply_markup=confirm_retell_keyboard().as_markup()
            )
        else:
            await anchor_manager.send_anchor(
                data.get("formatted_message")
            )
            await state.set_state(TaskStates.voice_message)
        await anchor_manager.delete_user_message(message)


@task_router.callback_query(F.data == "retry_voice_message")
async def retry_voice_message_handler(
        callback: CallbackQuery,
        state: FSMContext,
        anchor_manager: AnchorMessageManager
):
    await anchor_manager.delete_all_temp_messages()
    data = await state.get_data()

    formatted_message = data.get('formatted_message')

    if formatted_message:
        await anchor_manager.update_anchor_text(formatted_message)
    else:
        task_name = data.get('task_name')
        task_rules = data.get('task_rules')
        condition = data.get('condition')
        formatted_message = (
            f"Задание: <b><i>{task_name}</i></b>\n"
            f"<i>{task_rules}</i>\n"
            f"Твое слово: <b>{condition}</b>"
        )
        await anchor_manager.update_anchor_text(formatted_message)

    await state.set_state(TaskStates.voice_message)


@task_router.callback_query(F.data == "save_voice_message")
async def save_voice_message_handler(
        callback: CallbackQuery,
        user_repo: UserRepository,
        anchor_manager: AnchorMessageManager,
        progress_repo: ProgressRepository,
        state: FSMContext,
        completed_task_repo: CompletedTaskRepository
):
    try:
        data = await state.get_data()
        course_id = data.get("course_id")
        task_id = data.get("task_id")
        condition_id = data.get("condition_id")
        await anchor_manager.delete_all_temp_messages()
        user_streak, status = await user_repo.update_user_amount_of_days_series(callback.from_user.id)
        print("user streak", user_streak, " status: ", status)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        print("После получения user")
        keyboard = course_task_menu_keyboard()
        exp = await progress_repo.add_course_progress_to_user(
            user.id,
            course_id
        )
        print("После добавления прогресса пользователю")
        await completed_task_repo.add_completed_task_condition(
            telegram_id=callback.from_user.id,
            task_id=task_id,
            condition_id=condition_id
        )
        print("Дошли до if else status: ", status)
        if (status == StreakStatus.ALREADY_COMPLETED) or (status == StreakStatus.FIRST_TASK):
            await anchor_manager.edit_anchor(
                f"Упражнение засчитано!\n"
                f"Ты получил {exp} опыта",
                reply_markup=keyboard.as_markup()
            )
        elif status == StreakStatus.STREAK_BROKEN:
            await anchor_manager.edit_anchor(
                f"К сожалению, ты прервал серию, SpeechY очень разочарован\n"
                f"Но не волнуйся, одна ошибка, это не повод сдаваться!\n"
                f"Ты получил {exp} опыта",
                reply_markup=keyboard.as_markup()
            )

        elif status == StreakStatus.INCREASED:
            await anchor_manager.edit_anchor(
                f"Хорошая работа!\n"
                f"Твоя серия обновлена (текущая серия: {user.series_of_days_amount})\n"
                f"Продолжай в том же духе! Ты получил {exp} опыта",
                reply_markup=keyboard.as_markup()
            )

    except ValueError as e:
        await anchor_manager.edit_anchor(
            str(e)
        )


@task_router.callback_query(F.data == "confirm_retell")
async def confirm_retell_handler(
        callback: CallbackQuery,
        anchor_manager: AnchorMessageManager,
        state: FSMContext
):
    await anchor_manager.delete_all_temp_messages()
    await anchor_manager.edit_anchor(
        "Отлично! \nЖду твое голосовое сообщение!"
    )
    await state.set_state(TaskStates.voice_message)




from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from Managers.AnchorMessageManager import AnchorMessageManager
from database.repositories.ConditionRepository import ConditionRepository
from database.repositories.ProgressRepository import ProgressRepository
from database.repositories.TaskRepository import TaskRepository
from database.repositories.UserRepository import UserRepository
from keyboards.TaskKeyboards import back_to_profile_keyboard, confirm_retell_keyboard, back_to_task_menu_keyboard
from schemas.schemas import CourseName, DifficultyLevel, ImprovizationTaskName
from services.MessageFormatter import MessageFormatterFactory
from states.TaskStates import TaskStates


async def task_handler_factory(
        callback: CallbackQuery,
        task_repo: TaskRepository,
        condition_repo: ConditionRepository,
        progress_repo: ProgressRepository,
        user_repo: UserRepository,
        state: FSMContext,
        anchor_manager: AnchorMessageManager,
        course_name: CourseName
):
    """
    Generic task handler that works for any course
    :param callback:
    :param task_repo:
    :param condition_repo:
    :param progress_repo:
    :param user_repo:
    :param state:
    :param anchor_manager:
    :param course_name:
    :return:
    """

    try:
        task = await task_repo.get_random_task(course_name.value)
        if not task:
            await anchor_manager.edit_anchor(
                f"❌ Задания для курса {course_name.value} временно недоступны"
            )
            return

        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        user_progress = await progress_repo.get_user_course_progress(
            task.course_id,
            user.id
        )

        user_level = user_progress.difficulty_level if user_progress else DifficultyLevel.EASY

        condition = await condition_repo.get_random_condition_by_level(
            callback.from_user.id,
            task.id,
            user_level
        )
        if not condition:
            await anchor_manager.edit_anchor(
                "❌ Нет доступных заданий. Попробуйте позже.",
                reply_markup=back_to_profile_keyboard().as_markup()
            )
            return

        formatter = MessageFormatterFactory.get_formatter(course_name)
        message = formatter.format_task_message(task, condition)
        print("message: ", message)
        if task.name == ImprovizationTaskName.RETELL:

            await anchor_manager.edit_anchor(message,
                                             reply_markup=confirm_retell_keyboard().as_markup()
                                             )
        else:
            await anchor_manager.edit_anchor(message, reply_markup=back_to_task_menu_keyboard().as_markup())
        await state.update_data(
            task_id=task.id,
            task_name=task.name,
            task_rules=task.rules,
            condition=condition.condition,
            condition_id=condition.id,
            user_level=user_level,
            course_id=task.course_id,
            course_name=course_name.value,
            formatted_message=message
        )
        await state.set_state(TaskStates.voice_message)

    except ValueError as e:
        await anchor_manager.edit_anchor(f"❌ Ошибка: {str(e)}")
    except Exception as e:
        print(f"Error in task handler: {e}")
        await anchor_manager.edit_anchor(
            "❌ Произошла ошибка. Пожалуйста, попробуйте позже."
        )

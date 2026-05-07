from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def retry_voice_message_keyboard() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Сохранить",
            callback_data="save_voice_message",
            style="success"
        )

    )
    builder.row(
        InlineKeyboardButton(
            text="Записать еще раз",
            callback_data="retry_voice_message",
            style="primary"
        )
    )
    return builder


def task_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Импровизация",
            callback_data="task_improvisation",
            style="success"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Дикция",
            callback_data="task_diction",
            style="success"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Профиль",
            callback_data="get_profile",
            style="primary"
        )
    )
    return builder


def course_task_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Следующее",
            callback_data="task_improvisation",
            style="success"
        ),
        InlineKeyboardButton(
            text="Другой курс",
            callback_data="complete_tasks",
            style="primary"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Профиль",
            callback_data="get_profile",
            style="primary"
        )
    )
    return builder


def back_to_profile_keyboard() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Профиль",
            callback_data="get_profile",
            style="primary"
        )

    )
    return builder


def confirm_retell_keyboard() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Готов!",
            callback_data="confirm_retell",
            style="success"
        ),
        InlineKeyboardButton(
            text="Назад",
            callback_data="complete_tasks",
            style="primary"
        )
    )
    return builder


def back_to_task_menu_keyboard() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Назад",
            callback_data="complete_tasks",
            style="primary"
        )
    )
    return builder
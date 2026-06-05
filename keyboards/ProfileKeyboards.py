from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def profile_keyboard() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Пройти задания", callback_data="complete_tasks", style="success")
    )
    builder.row(
        InlineKeyboardButton(text="Изменить имя", callback_data="change_name", style="primary"),
        InlineKeyboardButton(text="Настроить уведомления", callback_data="configure_notifications", style="primary")
    )
    builder.row(
        InlineKeyboardButton(text="Реферальная система", callback_data="referral_system", style="primary")
    )
    builder.row(
        InlineKeyboardButton(text="Прислать голосовое", callback_data="send_voice_message", style="success")
    )

    return builder


def profile_back_keyboard() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Изменить позже", callback_data="get_profile", style="primary")
    )
    return builder


def change_notifications_keyboard(is_notifications_in: bool) -> InlineKeyboardBuilder:
    builder = profile_back_keyboard()
    if is_notifications_in:
        builder.row(
            InlineKeyboardButton(text="Выключить уведомления", callback_data="off_notifications", style="danger")
        )
    else:
        builder.row(
            InlineKeyboardButton(text="Включить уведомления", callback_data="off_notifications", style="success")
        )
    return builder

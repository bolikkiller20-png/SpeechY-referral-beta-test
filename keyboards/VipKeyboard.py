from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_vip_menu_keyboard() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Начать",
            callback_data="start_vip",
            style="success"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Купить попытки",
            callback_data="buy_trials",
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


def get_start_vip_keyboard() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Назад",
            callback_data="vip",
            style="primary"
        )
    )
    return builder

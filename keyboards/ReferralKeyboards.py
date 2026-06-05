from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def referral_main_keyboard() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="👥 Ввести код друга",
            callback_data="enter_referral",
            style="success"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🎁 Ввести промокод",
            callback_data="enter_promo_code",
            style="success"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="👤 Профиль",
            callback_data="get_profile",
            style="primary"
        )
    )
    return builder


def back_to_referral_system_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Назад",
            callback_data="referral_system",
            style="primary"
        )
    )
    return builder.as_markup()

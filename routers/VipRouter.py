from aiogram import Router, F
from aiogram.types import CallbackQuery

from Managers.AnchorMessageManager import AnchorMessageManager
from database.repositories.UserRepository import UserRepository
from keyboards.VipKeyboard import get_vip_menu_keyboard, get_start_vip_keyboard
from services.VipScenariosService import get_random_vip_scenario

vip_router = Router()


@vip_router.callback_query(F.data == "vip")
async def get_vip_menu(
        callback: CallbackQuery,
        anchor_manager: AnchorMessageManager,
        user_repo: UserRepository
):
    trial_amount = await user_repo.get_user_trials_amount(callback.from_user.id)
    await anchor_manager.edit_anchor(
        f"Добро пожаловать в VIP-версию бота\n"
        f"Здесь вы сможете прокачать свою речь по максимуму на реальном опыте, а не просто на упражнениях\n"
        f"Вам будут представлены некоторые сценарии (например, публичное выступление на какую-либо тему). "
        f"Вам необходимо будет пережить сценарий и записать голосовое вашего выступления.\n"
        f"Если готовы, нажимайте на Начать, чтобы всегда знать, что сказать в разных ситуациях\n\n"
        f"Количество попыток VIP-версии: <b>{trial_amount}</b>\n\n"
        f"Вы всегда можете приобрести попытки, нажав на соответсвующую кнопку",
        reply_markup=get_vip_menu_keyboard().as_markup()
    )


@vip_router.callback_query(F.data == "start_vip")
async def start_vip_handler(
        callback: CallbackQuery,
        anchor_manager: AnchorMessageManager
):
    scenario = await get_random_vip_scenario()
    await anchor_manager.edit_anchor(
        f"Сценарий: <b>{scenario['type']}</b>\n\n"
        f"Описание:\n"
        f" <i>{scenario['text']}</i>\n\n"
        f"<u>Жду твоего голосового сообщения</u>",
        reply_markup=get_start_vip_keyboard().as_markup()
    )

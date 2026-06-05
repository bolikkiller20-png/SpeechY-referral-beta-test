from aiogram.fsm.context import FSMContext

from database.repositories.PromoCodeRepository import PromoCodeRepository

from aiogram import Router, F
from aiogram.enums import ParseMode

from aiogram.types import CallbackQuery, Message

from Managers.AnchorMessageManager import AnchorMessageManager
from database.repositories.PromoCodeUsageRepository import PromoCodeUsageRepository
from database.repositories.ReferralRepository import ReferralRepository
from database.repositories.UserRepository import UserRepository
from database.services.promo_code import validate_promo_code
from keyboards.ReferralKeyboards import referral_main_keyboard, back_to_referral_system_menu
from keyboards.TaskKeyboards import back_to_profile_keyboard
from logger_config import app_logger
from schemas.schemas import PromoCodeTypes
from states.ReferralStates import ReferralStates

referral_router = Router()


@referral_router.callback_query(F.data == "referral_system")
async def referral_system_handler(
        callback: CallbackQuery,
        user_repo: UserRepository,
        anchor_manager: AnchorMessageManager,
        referral_repo: ReferralRepository
):
    print("Зашли в referral")
    referral_code = await referral_repo.create_referral_promo_code(
        callback.from_user.id
    )
    print(referral_code)
    invited_users = await referral_repo.get_all_referrals_by_promo_code_id(referral_code.id)
    print(invited_users)
    await anchor_manager.edit_anchor(
        f"🏆 <b>Добро пожаловать в реферальную систему!</b> 🏆\n\n"
        f"🔑 <b>Твой персональный код:</b> \n"
        f"<code>{referral_code.code}</code>\n"
        f"✨ <i>Нажми на код, чтобы скопировать</i>\n\n"
        f"📤 <b>Как получить бонус:</b>\n"
        f"1️⃣ Отправь код другу\n"
        f"2️⃣ Друг вводит код при регистрации\n"
        f"3️⃣ Вы оба получаете попытки на Pro-версию! 🎁\n\n"
        f"👥 Приглашено друзей: <b>{len(invited_users)}</b> из <b>{referral_code.max_uses}</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=referral_main_keyboard().as_markup()
    )


@referral_router.callback_query(F.data == "enter_referral")
async def enter_referral_handler(
        callback: CallbackQuery,
        anchor_manager: AnchorMessageManager,
        state: FSMContext
):
    await anchor_manager.edit_anchor(
        f"🎁 <b>Введи код друга</b>\n\n"
        f"Получи <b>1 бесплатную попытку</b> Pro-версии\n\n"
        f"👇 <i>Введите код ниже</i>",
        reply_markup=back_to_profile_keyboard().as_markup()
    )
    await state.set_state(ReferralStates.referral_code)


@referral_router.message(ReferralStates.referral_code)
async def validate_referral_code_handler(
        message: Message,
        state: FSMContext,
        anchor_manager: AnchorMessageManager,
        promo_code_repo: PromoCodeRepository,
        user_repo: UserRepository,
        referral_repo: ReferralRepository
):
    referral_code = message.text
    try:
        code = await promo_code_repo.get_promo_code(referral_code, is_referral=True)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        try:
            referral = await referral_repo.add_referral(
                inviter_id=code.owner_id,
                promo_code_id=code.id,
                invited_id=user.id
            )
            await anchor_manager.delete_user_message(message)
            await anchor_manager.edit_anchor(
                "✅ <b>Ты успешно активировал код друга</b>\n\n"
                "🎁 Ты получил дополнительную попытку <b>Pro-версии</b>",
                reply_markup=back_to_profile_keyboard().as_markup()
            )
            await state.set_state(None)

        except ValueError as e:
            await anchor_manager.edit_anchor(
                f"<b>{str(e)}</b>\n\n"
                f"Попробуй еще раз",
                reply_markup=back_to_profile_keyboard().as_markup()
            )
            await anchor_manager.delete_user_message(message)
    except ValueError as e:
        await anchor_manager.delete_user_message(message)
        await anchor_manager.edit_anchor(
            f"❌ <b>{str(e)}</b>\n\n"
            f"Попробуйте ввести код ещё раз 👇",
            reply_markup=back_to_profile_keyboard().as_markup()
        )


@referral_router.callback_query(F.data == "enter_promo_code")
async def enter_promo_code_handler(
        callback: CallbackQuery,
        anchor_manager: AnchorMessageManager,
        state: FSMContext
):
    await anchor_manager.edit_anchor(
        f"Введи промокод, чтобы получить приятные бонусы",
        reply_markup=back_to_referral_system_menu()
    )
    await state.set_state(ReferralStates.promo_code)


@referral_router.message(ReferralStates.promo_code)
async def process_promo_code_handler(
        message: Message,
        anchor_manager: AnchorMessageManager,
        promo_code_repo: PromoCodeRepository,
        user_repo: UserRepository,
        promo_code_usage_repo: PromoCodeUsageRepository,
        state: FSMContext
):
    try:

        promo_code = await validate_promo_code(
            message.text,
            message.from_user.id,
            promo_code_repo,
            user_repo,
            promo_code_usage_repo
        )
        promo_message = f"Промокод успешно активирован!\n\n"
        promo_message += f"Ты получил {promo_code.reward_value}% скидки на Pro-версию" if promo_code.reward_type == PromoCodeTypes.DISCOUNT.value else f"Ты получил {promo_code.reward_value} попыток на Pro-версию"
        await anchor_manager.edit_anchor(
            promo_message,
            reply_markup=back_to_referral_system_menu()
        )
        await anchor_manager.delete_user_message(message)
        await state.set_state(None)
    except ValueError as e:
        await anchor_manager.edit_anchor(
            f"{str(e)}\n\n"
            f"Попробуй еще раз",
            reply_markup=back_to_referral_system_menu()
        )
        await anchor_manager.delete_user_message(message)





from aiogram.fsm.state import StatesGroup, State


class ReferralStates(StatesGroup):
    referral_code = State()
    promo_code = State()
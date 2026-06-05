from database.models import PromoCode
from database.repositories.PromoCodeRepository import PromoCodeRepository
from database.repositories.PromoCodeUsageRepository import PromoCodeUsageRepository
from database.repositories.UserRepository import UserRepository
from schemas.schemas import PromoCodeTypes


async def validate_promo_code(
        code: str,
        telegram_id: int,
        promo_code_repo: PromoCodeRepository,
        user_repo: UserRepository,
        promo_code_usage_repo: PromoCodeUsageRepository
) -> PromoCode:
    print(code)
    promo_code = await promo_code_repo.get_promo_code(code, is_referral=False)
    if not promo_code:
        raise ValueError("Промокод не найден")
    if promo_code.used_count >= promo_code.max_uses:
        raise ValueError("Промокод уже использовали максимальное количетсво раз")
    user = await user_repo.get_by_telegram_id(telegram_id)
    promo_code_usage = await promo_code_usage_repo.get_promo_code_usage(
        promo_code.id,
        user.id
    )
    if promo_code_usage:
        raise ValueError("Вы уже использовали этот промокод!")
    else:
        await promo_code_usage_repo.add_promo_code_usage(
            promo_code.id,
            user.id
        )
        if promo_code.reward_type == PromoCodeTypes.DISCOUNT.value:
            await user_repo.update_user_pro_discount(user.id, promo_code.reward_value)
        elif promo_code.reward_type == PromoCodeTypes.TRIALS.value:
            await user_repo.update_trials_amount(user.id, promo_code.reward_value)
        return promo_code



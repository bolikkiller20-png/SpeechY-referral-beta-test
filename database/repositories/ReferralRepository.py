from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from constants.Constants import Constants, cons
from database.models import Referral, PromoCode
from database.repositories.PromoCodeRepository import PromoCodeRepository
from database.repositories.UserRepository import UserRepository
from schemas.schemas import PromoCodeTypes
from utils.ReferralUtils import ReferralUtils


class ReferralRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.promo_code_repo = PromoCodeRepository(session)

    async def create_referral_promo_code(
            self,
            telegram_id: int,
            reward_value: int = cons.get_referral_reward_value(),
            reward_type: PromoCodeTypes = PromoCodeTypes.TRIALS,
            max_uses: int = cons.get_referral_max_uses(),
    ) -> PromoCode:
        """Создаёт реферальный промокод для пользователя"""
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        code = ReferralUtils.generate_referral_code(user.id)
        return await self.promo_code_repo.get_or_create_promo_code(
            code=code,
            reward_type=reward_type,
            reward_value=reward_value,
            max_uses=max_uses,
            owner_id=user.id,
            is_referral=True
        )

    async def get_all_referrals_by_promo_code_id(
            self,
            promo_code_id: int
    ) -> List[Referral]:

        res = await self.session.execute(
            select(Referral)
            .where(Referral.promo_code_id == promo_code_id)
        )
        referrals = res.scalars().all()
        return list(referrals)

    async def add_referral(
            self,
            inviter_id: int,
            invited_id: int,
            promo_code_id: int
    ) -> Optional[Referral]:
        user = await self.user_repo.get_by_id(inviter_id)
        code = await self.promo_code_repo.get_promo_code_by_id(promo_code_id)
        if not code.is_active:
            raise ValueError("Промокод не активный")
        if invited_id == inviter_id:
            raise ValueError("Ты не можешь пригласить сам себя")

        print("Зашли в add_referral")
        res = await self.session.execute(
            select(Referral)
            .where(Referral.invited_id == invited_id)
        )
        referral = res.scalar_one_or_none()
        if referral:

            raise ValueError(f"Ты уже был приглашен пользователем: {user.name}")

        else:
            print(promo_code_id)
            print(inviter_id)
            print(invited_id)
            ref = Referral(
                promo_code_id=promo_code_id,
                inviter_id=inviter_id,
                invited_id=invited_id
            )
            success = await self.promo_code_repo.update_promo_code_used_count(promo_code_id=promo_code_id)
            if not success:
                raise ValueError("Лимит использований промокода исчерпан")
            self.session.add(ref)
            inviter_trials_count_success = await self.user_repo.update_trials_amount(
                ref.inviter_id,
                code.reward_value
            )
            invited_trials_count_success = await self.user_repo.update_trials_amount(
                ref.invited_id,
                code.reward_value
            )
            if not inviter_trials_count_success or not invited_trials_count_success:
                raise ValueError("Код активирован, но бонусы не начислены")
            await self.session.commit()
            return ref


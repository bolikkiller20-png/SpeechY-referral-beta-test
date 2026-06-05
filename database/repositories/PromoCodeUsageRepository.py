from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import PromoCodeUsage


class PromoCodeUsageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_promo_code_usage(
            self,
            promo_code_id: int,
            user_id: int
    ) -> Optional[PromoCodeUsage]:
        res = await self.session.execute(
            select(PromoCodeUsage)
            .where(PromoCodeUsage.promo_code_id == promo_code_id)
            .where(PromoCodeUsage.user_id == user_id)
        )
        return res.scalar_one_or_none()

    async def add_promo_code_usage(
            self,
            promo_code_id: int,
            user_id: int
    ) -> PromoCodeUsage:
        usage = await self.get_promo_code_usage(
            promo_code_id,
            user_id
        )
        if usage:
            raise ValueError("Вы уже использовали этот промокод!")
        else:
            promo_code_usage = PromoCodeUsage(
                promo_code_id=promo_code_id,
                user_id=user_id
            )
            self.session.add(promo_code_usage)
            await self.session.commit()
            return promo_code_usage


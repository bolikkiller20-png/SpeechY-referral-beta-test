from datetime import datetime
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import PromoCode
from schemas.schemas import PromoCodeTypes


class PromoCodeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_promo_code_by_id(self, id: int) -> Optional[PromoCode]:
        res = await self.session.execute(
            select(PromoCode)
            .where(PromoCode.id == id)
        )
        return res.scalar_one_or_none()

    async def update_promo_code_used_count(self, promo_code_id: int) -> int:
        res = await self.session.execute(
            update(PromoCode)
            .where(PromoCode.id == promo_code_id, PromoCode.used_count < PromoCode.max_uses)
            .values(used_count=PromoCode.used_count + 1)
        )
        await self.session.commit()
        return res.rowcount

    async def get_all_promo_codes(self):
        """
        Get all available promo_codes from db
        :return:
        all PromoCode objects from db
        """
        res = await self.session.execute(
            select(PromoCode)
        )
        return res.scalars().all()

    async def get_or_create_promo_code(
            self,
            code: str,
            reward_type: PromoCodeTypes,
            reward_value: int,
            max_uses: int,
            owner_id: int,
            is_referral: bool,
            expires_at: datetime = None,
            user_limit: int = 1,
            used_count: int = 0,
            is_active: bool = True,
    ) -> PromoCode:
        """Универсальный метод для получения или создания промокода"""
        existing = await self.get_promo_code(code, is_referral)
        print(existing)
        if not existing:
            print(owner_id)

            promo_code = PromoCode(
                owner_id=owner_id,
                code=code,
                reward_type=reward_type,
                reward_value=reward_value,
                max_uses=max_uses,
                used_count=used_count,
                expires_at=expires_at,
                user_limit=user_limit,
                is_active=is_active,
                is_referral=is_referral
            )
            self.session.add(promo_code)
            await self.session.commit()
            return promo_code
        else:
            return existing

    async def deactivate_expired_promo_codes(self) -> int:
        """
        Деактивирует просроченные промокоды
        Returns:
            количество деактивированных промокодов
        """
        from datetime import datetime

        result = await self.session.execute(
            select(PromoCode).where(
                PromoCode.expires_at < datetime.utcnow(),
                PromoCode.is_active == True
            )
        )
        expired_codes = result.scalars().all()

        for code in expired_codes:
            code.is_active = False
            print(f"Деактивирован просроченный промокод: {code.name}")

        await self.session.flush()
        return len(expired_codes)

    async def get_promo_code(
            self,
            code: str,
            is_referral: bool
    ) -> Optional[PromoCode]:
        res = await self.session.execute(
            select(PromoCode)
            .where(PromoCode.code == code)
            .where(PromoCode.is_referral == is_referral)
            .where(PromoCode.is_active == True)
        )
        promo_code = res.scalar_one_or_none()
        return promo_code



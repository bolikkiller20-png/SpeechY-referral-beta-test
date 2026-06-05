from datetime import datetime, time, date
from typing import Optional

from sqlalchemy import BigInteger, String, ForeignKey, DateTime, func, Time, Boolean, Integer, UniqueConstraint, \
    Computed, Date
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from schemas.schemas import DifficultyLevel, PromoCodeTypes


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    name: Mapped[str]
    username: Mapped[str]
    is_admin: Mapped[bool] = mapped_column(default=False)
    series_of_days_amount: Mapped[int] = mapped_column(default=0)
    notifications: Mapped[bool] = mapped_column(default=False)
    trial_amount: Mapped[int] = mapped_column(default=1, nullable=False)
    pro_discount: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=True
    )
    last_activity: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        onupdate=func.now(),
        nullable=True
    )

    last_task_completed_date: Mapped[Optional[date]] = mapped_column(
        Date,
        default=None,
        nullable=True
    )


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    notification_time: Mapped[time] = mapped_column(Time, nullable=False)


class Course(Base):
    __tablename__ = "courses"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class CompletedTask(Base):
    __tablename__ = "completed_tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    task_id: Mapped[int]
    condition_id: Mapped[int]


class Progress(Base):
    __tablename__ = "progress"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE")
    )
    progress: Mapped[int] = mapped_column(
        default=0
    )
    level: Mapped[int] = mapped_column(
        Computed("(progress / 10) + 1"),
        nullable=True
    )
    difficulty_level: Mapped[DifficultyLevel] = mapped_column(
        nullable=True,
        default=DifficultyLevel.EASY
    )


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )
    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    rules: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )


class Condition(Base):
    __tablename__ = "conditions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )
    task_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tasks.id", ondelete="CASCADE")
    )
    condition: Mapped[str] = mapped_column(
        String
    )
    difficulty_level: Mapped[DifficultyLevel] = mapped_column(
        nullable=True
    )


class UserAnchor(Base):
    __tablename__ = "user_anchors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    anchor_message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=True
    )


class PromoCode(Base):
    __tablename__ = "promo_codes"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    code: Mapped[str] = mapped_column(unique=True, index=True)
    reward_type: Mapped[PromoCodeTypes] = mapped_column()
    reward_value: Mapped[int] = mapped_column()
    max_uses: Mapped[int] = mapped_column()
    used_count: Mapped[int] = mapped_column(default=0)
    expires_at: Mapped[datetime] = mapped_column(nullable=True)
    user_limit: Mapped[int] = mapped_column(default=1)
    is_active: Mapped[bool] = mapped_column(nullable=True, default=False)
    is_referral: Mapped[bool] = mapped_column(default=False)


class Referral(Base):
    __tablename__ = "referrals"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    promo_code_id: Mapped[int] = mapped_column(ForeignKey("promo_codes.id"))
    inviter_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    invited_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=True
    )


class PromoCodeUsage(Base):
    __tablename__ = "promo_code_usages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    promo_code_id: Mapped[int] = mapped_column(ForeignKey("promo_codes.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    used_at: Mapped[datetime] = mapped_column(DateTime,
                                              server_default=func.now())
    __table_args__ = (
        UniqueConstraint('promo_code_id', 'user_id', name='unique_user_promo_usage'),
    )




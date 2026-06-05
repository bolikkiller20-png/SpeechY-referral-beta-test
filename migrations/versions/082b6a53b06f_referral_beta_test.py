"""Initial migration with all tables and referral beta test

Revision ID: 082b6a53b06f
Revises:
Create Date: 2026-06-05 22:36:59.803859

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM

# revision identifiers, used by Alembic.
revision: str = '082b6a53b06f'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создаем ENUM типы
    difficulty_level_enum = ENUM('easy', 'medium', 'hard', name='difficultylevel', create_type=True)
    difficulty_level_enum.create(op.get_bind(), checkfirst=True)

    promo_code_types_enum = ENUM('discount', 'trials', name='promocodetypes', create_type=True)
    promo_code_types_enum.create(op.get_bind(), checkfirst=True)

    # 1. Таблица users
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('series_of_days_amount', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('notifications', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('trial_amount', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('pro_discount', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('last_activity', sa.DateTime(), nullable=True),
        sa.Column('last_task_completed_date', sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_id')
    )
    op.create_index('ix_users_telegram_id', 'users', ['telegram_id'])

    # 2. Таблица courses
    op.create_table('courses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id')
    )

    # Добавляем курсы
    op.execute("INSERT INTO courses (name, description, is_active) VALUES ('Импровизация', 'Курс по развитию навыков импровизации', true)")
    op.execute("INSERT INTO courses (name, description, is_active) VALUES ('Дикция', 'Курс по улучшению дикции и речи', true)")

    # 3. Таблица notifications
    op.create_table('notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('notification_time', sa.Time(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 4. Таблица tasks
    op.create_table('tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('rules', sa.String(200), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 5. Таблица completed_tasks
    op.create_table('completed_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('condition_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 6. Таблица progress
    op.create_table('progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('level', sa.Integer(), computed="(progress / 10) + 1"),
        sa.Column('difficulty_level', difficulty_level_enum, nullable=True, server_default='easy'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 7. Таблица conditions
    op.create_table('conditions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('condition', sa.String(), nullable=False),
        sa.Column('difficulty_level', difficulty_level_enum, nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 8. Таблица user_anchors
    op.create_table('user_anchors',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('chat_id', sa.BigInteger(), nullable=False),
        sa.Column('anchor_message_id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 9. Таблица promo_codes
    op.create_table('promo_codes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('reward_type', promo_code_types_enum, nullable=False),
        sa.Column('reward_value', sa.Integer(), nullable=False),
        sa.Column('max_uses', sa.Integer(), nullable=False),
        sa.Column('used_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('user_limit', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('is_referral', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index('ix_promo_codes_code', 'promo_codes', ['code'])

    # 10. Таблица referrals
    op.create_table('referrals',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('promo_code_id', sa.Integer(), nullable=False),
        sa.Column('inviter_id', sa.Integer(), nullable=False),
        sa.Column('invited_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['invited_id'], ['users.id']),
        sa.ForeignKeyConstraint(['inviter_id'], ['users.id']),
        sa.ForeignKeyConstraint(['promo_code_id'], ['promo_codes.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('invited_id')
    )

    # 11. Таблица promo_code_usages
    op.create_table('promo_code_usages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('promo_code_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('used_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['promo_code_id'], ['promo_codes.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('promo_code_id', 'user_id', name='unique_user_promo_usage')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('promo_code_usages')
    op.drop_table('referrals')
    op.drop_index('ix_promo_codes_code', table_name='promo_codes')
    op.drop_table('promo_codes')
    op.drop_table('user_anchors')
    op.drop_table('conditions')
    op.drop_table('progress')
    op.drop_table('completed_tasks')
    op.drop_table('tasks')
    op.drop_table('notifications')
    op.drop_table('courses')
    op.drop_index('ix_users_telegram_id', table_name='users')
    op.drop_table('users')

    # Удаляем ENUM типы
    sa.Enum(name='difficultylevel').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='promocodetypes').drop(op.get_bind(), checkfirst=True)
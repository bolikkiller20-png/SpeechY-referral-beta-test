"""added new column for users

Revision ID: 54300f84e2db
Revises: 4ec5686fe365
Create Date: 2026-07-20 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '54300f84e2db'
down_revision: Union[str, None] = '4ec5686fe365'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Сначала добавляем колонку с DEFAULT значением
    op.add_column('users', sa.Column('vip_trials', sa.Integer(), server_default='0', nullable=False))


def downgrade() -> None:
    op.drop_column('users', 'vip_trials')
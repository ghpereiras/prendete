"""add user language preference

Revision ID: 09f21baaf70a
Revises: 9904cb114eee
Create Date: 2026-09-29 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '09f21baaf70a'
down_revision: Union[str, None] = '9904cb114eee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('language', sa.String(length=5), nullable=False, server_default='es'),
    )


def downgrade() -> None:
    op.drop_column('users', 'language')

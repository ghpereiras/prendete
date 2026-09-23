"""event duration and registration deadline

Revision ID: 3a47b6f2ea14
Revises: a34621deec80
Create Date: 2026-09-23 18:24:00.487811

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3a47b6f2ea14'
down_revision: Union[str, None] = 'a34621deec80'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('events', sa.Column('duration_minutes', sa.Integer(), nullable=True))
    op.add_column('events', sa.Column('registration_deadline_minutes_before', sa.Integer(), nullable=True))

    # Backfill duration_minutes for existing rows from the ends_at column before dropping it.
    op.execute(
        "UPDATE events SET duration_minutes = "
        "GREATEST(1, CEIL(EXTRACT(EPOCH FROM (ends_at - starts_at)) / 60))::integer"
    )

    op.alter_column('events', 'duration_minutes', nullable=False)
    op.drop_column('events', 'ends_at')


def downgrade() -> None:
    op.add_column('events', sa.Column('ends_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.execute("UPDATE events SET ends_at = starts_at + (duration_minutes || ' minutes')::interval")
    op.alter_column('events', 'ends_at', nullable=False)

    op.drop_column('events', 'registration_deadline_minutes_before')
    op.drop_column('events', 'duration_minutes')

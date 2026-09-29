"""make max_attendees optional (unlimited events)

Revision ID: 9904cb114eee
Revises: 9e65436576ce
Create Date: 2026-09-29 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9904cb114eee'
down_revision: Union[str, None] = '9e65436576ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('events', 'max_attendees', existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    # Existing unlimited events (NULL) need a value before the column can go
    # back to NOT NULL — pick an arbitrary large cap rather than losing rows.
    op.execute("UPDATE events SET max_attendees = 999999 WHERE max_attendees IS NULL")
    op.alter_column('events', 'max_attendees', existing_type=sa.Integer(), nullable=False)

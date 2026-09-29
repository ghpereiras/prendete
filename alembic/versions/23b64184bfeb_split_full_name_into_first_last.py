"""split full_name into first_name/last_name

Revision ID: 23b64184bfeb
Revises: bfea6845a4be
Create Date: 2026-09-29 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '23b64184bfeb'
down_revision: Union[str, None] = 'bfea6845a4be'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('first_name', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('last_name', sa.String(length=255), nullable=True))

    # Backfill from the existing full_name: everything before the first
    # space becomes first_name, the rest becomes last_name (empty string if
    # there was no space at all).
    users = sa.table(
        'users',
        sa.column('id', sa.Integer),
        sa.column('full_name', sa.String),
        sa.column('first_name', sa.String),
        sa.column('last_name', sa.String),
    )
    connection = op.get_bind()
    for user_id, full_name in connection.execute(sa.select(users.c.id, users.c.full_name)):
        first_name, _, last_name = full_name.partition(' ')
        connection.execute(
            users.update()
            .where(users.c.id == user_id)
            .values(first_name=first_name, last_name=last_name)
        )

    op.alter_column('users', 'first_name', nullable=False)
    op.alter_column('users', 'last_name', nullable=False)
    op.drop_column('users', 'full_name')


def downgrade() -> None:
    op.add_column('users', sa.Column('full_name', sa.String(length=255), nullable=True))

    users = sa.table(
        'users',
        sa.column('id', sa.Integer),
        sa.column('full_name', sa.String),
        sa.column('first_name', sa.String),
        sa.column('last_name', sa.String),
    )
    connection = op.get_bind()
    for user_id, first_name, last_name in connection.execute(
        sa.select(users.c.id, users.c.first_name, users.c.last_name)
    ):
        full_name = f"{first_name} {last_name}".strip()
        connection.execute(
            users.update().where(users.c.id == user_id).values(full_name=full_name)
        )

    op.alter_column('users', 'full_name', nullable=False)
    op.drop_column('users', 'first_name')
    op.drop_column('users', 'last_name')

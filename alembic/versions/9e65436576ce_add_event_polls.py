"""add event polls

Revision ID: 9e65436576ce
Revises: 23b64184bfeb
Create Date: 2026-09-29 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e65436576ce'
down_revision: Union[str, None] = '23b64184bfeb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'event_polls',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('location_details', sa.String(length=255), nullable=True),
        sa.Column('maps_link', sa.String(length=2048), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('invite_token', sa.String(length=32), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('resulting_event_id', sa.Integer(), nullable=True),
        sa.Column('resolved_date_option_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resulting_event_id'], ['events.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_event_polls_invite_token'), 'event_polls', ['invite_token'], unique=True)

    op.create_table(
        'event_poll_date_options',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('poll_id', sa.Integer(), nullable=False),
        sa.Column('starts_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['poll_id'], ['event_polls.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_foreign_key(
        'fk_event_polls_resolved_date_option_id',
        'event_polls',
        'event_poll_date_options',
        ['resolved_date_option_id'],
        ['id'],
        ondelete='SET NULL',
    )

    op.create_table(
        'event_poll_votes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date_option_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['date_option_id'], ['event_poll_date_options.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date_option_id', 'user_id', name='uq_date_option_user'),
    )


def downgrade() -> None:
    op.drop_table('event_poll_votes')
    op.drop_constraint('fk_event_polls_resolved_date_option_id', 'event_polls', type_='foreignkey')
    op.drop_table('event_poll_date_options')
    op.drop_index(op.f('ix_event_polls_invite_token'), table_name='event_polls')
    op.drop_table('event_polls')

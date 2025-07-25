"""add schedule fields to users

Revision ID: 62577725e0b0
Revises: 0001
Create Date: 2025-07-25 08:58:08.212733

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '62577725e0b0'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add schedule fields to users table
    op.add_column('users', sa.Column('schedule_start', sa.Time(), nullable=True))
    op.add_column('users', sa.Column('schedule_end', sa.Time(), nullable=True))


def downgrade() -> None:
    # Remove schedule fields from users table
    op.drop_column('users', 'schedule_end')
    op.drop_column('users', 'schedule_start') 
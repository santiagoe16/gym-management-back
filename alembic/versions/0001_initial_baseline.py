"""Initial baseline - mark current database state

Revision ID: 0001
Revises: 
Create Date: 2025-07-23 20:35:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This is a baseline migration - no changes needed
    # The database already exists with the current schema
    pass


def downgrade() -> None:
    # This is a baseline migration - no changes needed
    pass 
"""ml_column_created_by

Revision ID: f89eee7c0a44
Revises: d9087f8e950e
Create Date: 2024-07-11 15:43:24.469310

"""
import sqlalchemy as sa

from alembic import op



# revision identifiers, used by Alembic.
revision = 'f89eee7c0a44'
down_revision = 'd9087f8e950e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('ml', sa.Column('created_by', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('ml', 'created_by')

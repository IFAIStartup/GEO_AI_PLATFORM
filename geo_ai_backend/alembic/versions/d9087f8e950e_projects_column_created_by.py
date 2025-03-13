"""projects_column_created_by

Revision ID: d9087f8e950e
Revises: c8970effcfe4
Create Date: 2024-07-11 15:34:12.764599

"""
import sqlalchemy as sa

from alembic import op



# revision identifiers, used by Alembic.
revision = 'd9087f8e950e'
down_revision = '67741e6b5dd9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('projects', sa.Column('created_by', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('projects', 'created_by')

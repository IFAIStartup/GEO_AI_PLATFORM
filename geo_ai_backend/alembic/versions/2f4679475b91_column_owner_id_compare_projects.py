"""column_owner_id_compare_projects

Revision ID: 2f4679475b91
Revises: ff013fdb3f9e
Create Date: 2024-12-04 20:03:19.979880

"""
import sqlalchemy as sa

from alembic import op



# revision identifiers, used by Alembic.
revision = '2f4679475b91'
down_revision = 'ff013fdb3f9e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('compare_projects', sa.Column('owner_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('compare_projects', 'owner_id')


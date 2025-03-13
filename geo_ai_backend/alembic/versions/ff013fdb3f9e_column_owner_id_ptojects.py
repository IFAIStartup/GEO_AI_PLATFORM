"""column_owner_id_ptojects

Revision ID: ff013fdb3f9e
Revises: 4688bb386ffc
Create Date: 2024-12-04 19:57:00.954087

"""
import sqlalchemy as sa

from alembic import op



# revision identifiers, used by Alembic.
revision = 'ff013fdb3f9e'
down_revision = 'a273775e673a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('projects', sa.Column('owner_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('projects', 'owner_id')

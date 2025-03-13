"""column_owner_id_error_history

Revision ID: 6b9b514d0454
Revises: 2394d48131ae
Create Date: 2024-12-06 12:41:19.882209

"""
import sqlalchemy as sa

from alembic import op



# revision identifiers, used by Alembic.
revision = '6b9b514d0454'
down_revision = '2394d48131ae'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('error_history', sa.Column('owner_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('error_history', 'owner_id')

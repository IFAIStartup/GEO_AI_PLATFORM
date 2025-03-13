"""column_owner_id_action_history

Revision ID: 2394d48131ae
Revises: 2f4679475b91
Create Date: 2024-12-06 12:38:34.797114

"""
import sqlalchemy as sa

from alembic import op



# revision identifiers, used by Alembic.
revision = '2394d48131ae'
down_revision = '2f4679475b91'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('action_history', sa.Column('owner_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('action_history', 'owner_id')

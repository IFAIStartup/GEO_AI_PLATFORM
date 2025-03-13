"""project_id_history

Revision ID: 037228548b8a
Revises: fa3f91dce7c1
Create Date: 2024-10-31 15:29:43.487876

"""
import sqlalchemy as sa

from alembic import op



# revision identifiers, used by Alembic.
revision = '037228548b8a'
down_revision = 'bffae15bf446'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("action_history", sa.Column("project_id", sa.Integer(), nullable=True))
    op.add_column("error_history", sa.Column("project_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('action_history', 'project_id')
    op.drop_column('error_history', 'project_id')

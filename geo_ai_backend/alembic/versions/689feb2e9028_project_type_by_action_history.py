"""project_type_by_action_history

Revision ID: 689feb2e9028
Revises: 4688bb386ffc
Create Date: 2024-12-10 13:38:19.127074

"""
import sqlalchemy as sa

from alembic import op



# revision identifiers, used by Alembic.
revision = '689feb2e9028'
down_revision = '4688bb386ffc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("action_history", sa.Column("project_type", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('action_history', 'project_type')

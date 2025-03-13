"""project_type_by_error_history

Revision ID: a273775e673a
Revises: 689feb2e9028
Create Date: 2024-12-10 13:42:55.298913

"""
import sqlalchemy as sa

from alembic import op



# revision identifiers, used by Alembic.
revision = 'a273775e673a'
down_revision = '689feb2e9028'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("error_history", sa.Column("project_type", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('error_history', 'project_type')

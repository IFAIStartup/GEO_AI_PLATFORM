"""code_error_history

Revision ID: ab31e9feb245
Revises: ceda4c2405c4
Create Date: 2024-10-03 13:40:32.920822

"""
import sqlalchemy as sa

from alembic import op



# revision identifiers, used by Alembic.
revision = 'ab31e9feb245'
down_revision = 'ceda4c2405c4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("error_history", sa.Column("code", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('error_history', 'code')

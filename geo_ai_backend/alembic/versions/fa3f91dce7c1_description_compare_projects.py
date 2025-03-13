"""description_compare_projects

Revision ID: fa3f91dce7c1
Revises: a0e8db95fdea
Create Date: 2024-10-25 11:26:42.126210

"""
import sqlalchemy as sa

from alembic import op



# revision identifiers, used by Alembic.
revision = 'fa3f91dce7c1'
down_revision = 'a0e8db95fdea'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "compare_projects", sa.Column("description", sa.String(), nullable=True)
    )
    op.add_column(
        "compare_projects", sa.Column("error_code", sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('compare_projects', 'description')
    op.drop_column('compare_projects', 'error_code')

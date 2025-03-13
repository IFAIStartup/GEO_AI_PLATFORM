"""description_project

Revision ID: a0e8db95fdea
Revises: ab31e9feb245
Create Date: 2024-10-23 18:27:31.684005

"""
import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision = 'a0e8db95fdea'
down_revision = 'eeff5d5e85c5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "projects", sa.Column("description", sa.String(), nullable=True)
    )
    op.add_column(
        "projects", sa.Column("error_code", sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('projects', 'description')
    op.drop_column('projects', 'error_code')

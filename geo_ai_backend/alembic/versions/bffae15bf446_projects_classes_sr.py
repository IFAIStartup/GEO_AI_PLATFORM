"""projects_classes_sr

Revision ID: bffae15bf446
Revises: fa3f91dce7c1
Create Date: 2024-10-31 15:11:27.831165

"""
import sqlalchemy as sa

from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'bffae15bf446'
down_revision = 'fa3f91dce7c1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "projects", sa.Column("classes", postgresql.ARRAY(sa.String), nullable=True)
    )
    op.add_column(
        "projects", sa.Column("super_resolution", sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('projects', 'classes')
    op.drop_column('projects', 'super_resolution')

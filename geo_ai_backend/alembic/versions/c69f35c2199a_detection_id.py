"""detection_id

Revision ID: c69f35c2199a
Revises: aac4e54d4af2
Create Date: 2023-10-09 22:57:36.188086

"""
import sqlalchemy as sa

from alembic import op

from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c69f35c2199a'
down_revision = 'aac4e54d4af2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "projects",
        sa.Column("detection_id", sa.String(), nullable=True, server_default=None)
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("projects", "detection_id")
    # ### end Alembic commands ###

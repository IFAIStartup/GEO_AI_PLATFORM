"""project task result

Revision ID: 1a9d329d75e2
Revises: 6075461333f0
Create Date: 2023-11-27 10:28:48.349623

"""
import sqlalchemy as sa

from alembic import op

from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1a9d329d75e2'
down_revision = '6075461333f0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("projects", sa.Column("task_result", postgresql.JSONB, nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("projects", "task_result")
    # ### end Alembic commands ###

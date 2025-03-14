"""compare shooting date

Revision ID: b794cb054f1c
Revises: 75014a2b15f0
Create Date: 2024-02-19 18:05:22.810765

"""
import sqlalchemy as sa

from alembic import op

from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b794cb054f1c'
down_revision = 'af47368c6bbc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('compare_projects', sa.Column('shooting_date_1', sa.String(), nullable=True))
    op.add_column('compare_projects', sa.Column('shooting_date_2', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('compare_projects', 'shooting_date_1')
    op.drop_column('compare_projects', 'shooting_date_2')
    # ### end Alembic commands ###

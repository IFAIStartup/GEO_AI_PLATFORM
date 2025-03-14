"""project input file

Revision ID: a2c56b4edee0
Revises: 59949d09fb54
Create Date: 2024-01-15 17:45:42.571913

"""
import sqlalchemy as sa

from alembic import op

from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a2c56b4edee0'
down_revision = '59949d09fb54'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('projects', sa.Column('input_files', sa.JSON(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('projects', 'input_files')
    # ### end Alembic commands ###

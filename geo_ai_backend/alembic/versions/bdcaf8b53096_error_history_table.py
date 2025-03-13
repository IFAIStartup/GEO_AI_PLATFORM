"""error_history_table

Revision ID: bdcaf8b53096
Revises: 8cd1dd92441f
Create Date: 2024-09-09 17:30:58.307884

"""
import sqlalchemy as sa

from alembic import op



# revision identifiers, used by Alembic.
revision = 'bdcaf8b53096'
down_revision = '8cd1dd92441f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('error_history',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=False),
                    sa.Column('user_action', sa.String(), nullable=False),
                    sa.Column('username', sa.String(), nullable=False),
                    sa.Column('project', sa.String(), nullable=False),
                    sa.Column('description', sa.String(), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    )
    op.create_index(op.f('ix_error_history_id'), 'error_history', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_error_history_id'), table_name='error_history')
    op.drop_table('error_history')

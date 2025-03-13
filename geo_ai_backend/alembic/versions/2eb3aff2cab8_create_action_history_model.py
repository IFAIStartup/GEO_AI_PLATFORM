"""create_action_history_model

Revision ID: 2eb3aff2cab8
Revises: c69f35c2199a
Create Date: 2023-11-19 22:27:45.104803

"""
import sqlalchemy as sa

from alembic import op



# revision identifiers, used by Alembic.
revision = '2eb3aff2cab8'
down_revision = 'c69f35c2199a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('action_history',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=False),
                    sa.Column('user_action', sa.String(), nullable=False),
                    sa.Column('username', sa.String(), nullable=False),
                    sa.Column('project', sa.String(), nullable=False),
                    sa.Column('description', sa.String(), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    )
    op.create_index(op.f('ix_history_id'), 'action_history', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_history_id'), table_name='action_history')
    op.drop_table('action_history')

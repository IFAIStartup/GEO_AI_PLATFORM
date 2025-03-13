"""create_objects_history_model

Revision ID: 6075461333f0
Revises: 2eb3aff2cab8
Create Date: 2023-11-19 22:49:40.424503

"""
import sqlalchemy as sa

from alembic import op



# revision identifiers, used by Alembic.
revision = '6075461333f0'
down_revision = '2eb3aff2cab8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('objects_history',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=False),
                    sa.Column('object_name', sa.String(), nullable=False),
                    sa.Column('action', sa.String(), nullable=False),
                    sa.Column('username', sa.String(), nullable=False),
                    sa.Column('project', sa.String(), nullable=False),
                    sa.Column('description', sa.String(), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    )
    op.create_index(
        op.f('ix_objects_history_id'), 'objects_history', ['id'], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_objects_history_id'), table_name='objects_history')
    op.drop_table('objects_history')

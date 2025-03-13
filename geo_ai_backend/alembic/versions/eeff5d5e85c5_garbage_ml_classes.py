"""garbage_ml_classes

Revision ID: eeff5d5e85c5
Revises: 46cb84ee44fc
Create Date: 2024-10-29 18:34:21.197425

"""
import sqlalchemy as sa

from alembic import op



# revision identifiers, used by Alembic.
revision = 'eeff5d5e85c5'
down_revision = '46cb84ee44fc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
            INSERT
            INTO ml_classes(name, type_of_objects, created_at)
            VALUES(
            'garbage',
            array[
                'household_garbage',
                'construction_garbage',
                'natural_garbage',
                'furniture_garbage',
                'others'
                ],
            '2024-10-29 00:00:01.000'
            );
            """
    )


def downgrade() -> None:
    op.execute("DELETE FROM ml_classes WHERE name='garbage'")

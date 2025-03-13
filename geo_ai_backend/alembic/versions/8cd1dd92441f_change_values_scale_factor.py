"""change_values_scale_factor

Revision ID: 8cd1dd92441f
Revises: f50e70729410
Create Date: 2024-07-19 10:56:35.533223

"""
import sqlalchemy as sa

from alembic import op



# revision identifiers, used by Alembic.
revision = '8cd1dd92441f'
down_revision = 'f50e70729410'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
            UPDATE ml
            SET scale_factor = 0.625
            WHERE type_of_data @> '{"aerial_images"}' AND view = 'deeplabv3'
        """
    )


def downgrade() -> None:
    op.execute(
        """
            UPDATE ml
            SET scale_factor = 1
            WHERE type_of_data @> '{"aerial_images"}' AND view = 'deeplabv3'
        """
    )

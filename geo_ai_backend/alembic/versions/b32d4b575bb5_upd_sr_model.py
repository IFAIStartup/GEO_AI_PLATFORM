"""upd_sr_model

Revision ID: b32d4b575bb5
Revises: 768a759c36d3
Create Date: 2024-03-13 16:39:04.736191

"""
import sqlalchemy as sa

from alembic import op



# revision identifiers, used by Alembic.
revision = 'b32d4b575bb5'
down_revision = '768a759c36d3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
            UPDATE ml
            SET constant = true,
                type_of_data =  array['aerial_images', 'satellite_images']
            WHERE name = 'Aerial_HAT-L_SRx2_8985';
        """
    )
    op.execute(
        """
            UPDATE ml
            SET constant = true,
                type_of_data =  array['aerial_images', 'satellite_images']
            WHERE name = 'Aerial_HAT-L_SRx3_8985';
        """
    )
    op.execute(
        """
            UPDATE ml
            SET constant = true,
                type_of_data =  array['aerial_images', 'satellite_images']
            WHERE name = 'Aerial_HAT-L_SRx4_11980';
        """
    )


def downgrade() -> None:
    op.execute(
        """
            UPDATE ml
            SET constant = False,
                type_of_data =  array['super_resolution']
            WHERE name = 'Aerial_HAT-L_SRx2_8985';
        """
    )
    op.execute(
        """
            UPDATE ml
            SET constant = False,
                type_of_data =  array['super_resolution']
            WHERE name = 'Aerial_HAT-L_SRx3_8985';
        """
    )
    op.execute(
        """
            UPDATE ml
            SET constant = False,
                type_of_data =  array['super_resolution']
            WHERE name = 'Aerial_HAT-L_SRx4_11980';
        """
    )

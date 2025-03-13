"""change_params_garbage

Revision ID: 46cb84ee44fc
Revises: ceda4c2405c4
Create Date: 2024-10-01 11:17:58.997619

"""
import sqlalchemy as sa

from alembic import op



# revision identifiers, used by Alembic.
revision = '46cb84ee44fc'
down_revision = 'ab31e9feb245'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
            UPDATE ml
            SET view = 'yolov8_det',
                tile_size = 640,
                scale_factor = 0,
                type_of_data = array['garbage']
            WHERE name = 'yolov8s_garbage_29102023';
        """
    )


def downgrade() -> None:
    op.execute(
        """
            UPDATE ml
            SET view = 'yolov8',
                tile_size = 1280,
                scale_factor = 1,
                type_of_data = array['panorama_360']
            WHERE name = 'yolov8s_garbage_29102023';
        """
    )

"""additional_ml_models_params

Revision ID: f6c4e2da192c
Revises: 347699a03658
Create Date: 2024-06-27 12:33:46.781111

"""
import sqlalchemy as sa

from alembic import op



# revision identifiers, used by Alembic.
revision = 'f6c4e2da192c'
down_revision = 'f89eee7c0a44'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ml", sa.Column("tile_size", sa.Integer(), nullable=True))
    op.add_column("ml", sa.Column("scale_factor", sa.Float(), nullable=True))
    op.execute(
        """
            UPDATE ml
            SET tile_size = 1024, scale_factor = 1.0
            WHERE type_of_data = '{aerial_images}' AND view = 'yolov8';
        """
    )
    op.execute(
        """
            UPDATE ml
            SET tile_size = 640, scale_factor = 1.0
            WHERE type_of_data = '{aerial_images}' AND view = 'deeplabv3';
        """
    )
    op.execute(
        """
            UPDATE ml
            SET tile_size = 640, scale_factor = 1.0
            WHERE type_of_data = '{satellite_images}' AND view = 'yolov8';
        """
    )
    op.execute(
        """
            UPDATE ml
            SET tile_size = 640, scale_factor = 1.0
            WHERE type_of_data = '{satellite_images}' AND view = 'deeplabv3';
        """
    )
    op.execute(
        """
            UPDATE ml
            SET tile_size = 1280, scale_factor = 1.0
            WHERE type_of_data = '{panorama_360}' AND view = 'yolov8';
        """
    )
    op.execute(
        """
            UPDATE ml
            SET tile_size = 640, scale_factor = 1.0
            WHERE type_of_data = '{panorama_360}' AND view = 'deeplabv3';
        """
    )


def downgrade() -> None:
    op.drop_column("ml", "tile_size")
    op.drop_column("ml", "scale_factor")

"""new_model_garbage

Revision ID: ef677655dabf
Revises: 8cd1dd92441f
Create Date: 2024-09-18 05:49:28.260701

"""
import sqlalchemy as sa

from alembic import op



# revision identifiers, used by Alembic.
revision = 'ef677655dabf'
down_revision = 'bdcaf8b53096'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
            INSERT
            INTO ml(name, link, type_of_data, type_of_objects, default_model, constant, created_at, status, view, tile_size, scale_factor)
            VALUES('yolov8s_garbage_29102023', 'yolov8s_garbage_29102023', array['panorama_360'],array['household_garbage', 'construction_garbage', 'natural_garbage', 'furniture_garbage', 'others'], true, false, '2024-08-06 00:00:01.000', 'Ready to use', 'yolov8', 1280, 1.0);
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM ml WHERE name='yolov8s_garbage_29102023'")

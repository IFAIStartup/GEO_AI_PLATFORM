"""new_model_yolo_aerial

Revision ID: ceda4c2405c4
Revises: aba0a711e7c7
Create Date: 2024-09-18 06:30:02.846714

"""
import sqlalchemy as sa

from alembic import op



# revision identifiers, used by Alembic.
revision = 'ceda4c2405c4'
down_revision = 'aba0a711e7c7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
            INSERT
            INTO ml(name, link, type_of_data, type_of_objects, default_model, constant, created_at, status, view, tile_size, scale_factor)
            VALUES('aerial_building_05092024', 'aerial_building_05092024', array['aerial_images'], array['buildings'], false, false, '2024-09-01 00:00:01.000', 'Ready to use', 'yolov8', 1280, 0.5);
            """
    )

    op.execute(
        """
            INSERT
            INTO ml(name, link, type_of_data, type_of_objects, default_model, constant, created_at, status, view, tile_size, scale_factor)
            VALUES('aerial_trees_05092024', 'aerial_trees_05092024', array['aerial_images'], array['trees'], false, false, '2024-09-01 00:00:01.000', 'Ready to use', 'yolov8', 1280, 1.0);
            """
    )

    op.execute(
        """
            INSERT
            INTO ml(name, link, type_of_data, type_of_objects, default_model, constant, created_at, status, view, tile_size, scale_factor)
            VALUES('aerial_palm_tree_05092024', 'aerial_palm_tree_05092024', array['aerial_images'], array['palm_tree'], false, false, '2024-09-01 00:00:01.000', 'Ready to use', 'yolov8', 640, 0.5);
            """
    )

    op.execute(
        """
            INSERT
            INTO ml(name, link, type_of_data, type_of_objects, default_model, constant, created_at, status, view, tile_size, scale_factor)
            VALUES('aerial_farms_09092024', 'aerial_farms_09092024', array['aerial_images'], array['farms'], false, false, '2024-09-01 00:00:01.000', 'Ready to use', 'yolov8', 640, 0.125);
            """
    )


def downgrade() -> None:
    op.execute("DELETE FROM ml WHERE name='aerial_building_05092024'")
    op.execute("DELETE FROM ml WHERE name='aerial_trees_05092024'")
    op.execute("DELETE FROM ml WHERE name='aerial_palm_tree_05092024'")
    op.execute("DELETE FROM ml WHERE name='aerial_farms_09092024'")


"""new_model_yolo_aerial_satellite

Revision ID: aba0a711e7c7
Revises: ef677655dabf
Create Date: 2024-09-18 05:57:30.640235

"""
import sqlalchemy as sa

from alembic import op



# revision identifiers, used by Alembic.
revision = 'aba0a711e7c7'
down_revision = 'ef677655dabf'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
            INSERT
            INTO ml(name, link, type_of_data, type_of_objects, default_model, constant, created_at, status, view, tile_size, scale_factor)
            VALUES('aerial_building', 'aerial_building', array['aerial_images'], array['buildings'], false, false, '2024-06-01 00:00:01.000', 'Ready to use', 'yolov8', 1280, 0.5);
            """
    )

    op.execute(
        """
            INSERT
            INTO ml(name, link, type_of_data, type_of_objects, default_model, constant, created_at, status, view, tile_size, scale_factor)
            VALUES('aerial_trees', 'aerial_trees', array['aerial_images'], array['trees'], false, false, '2024-06-01 00:00:01.000', 'Ready to use', 'yolov8', 1280, 1.0);
            """
    )

    op.execute(
        """
            INSERT
            INTO ml(name, link, type_of_data, type_of_objects, default_model, constant, created_at, status, view, tile_size, scale_factor)
            VALUES('aerial_palm_tree', 'aerial_palm_tree', array['aerial_images'], array['palm_tree'], false, false, '2024-06-01 00:00:01.000', 'Ready to use', 'yolov8', 640, 0.5);
            """
    )

    op.execute(
        """
            INSERT
            INTO ml(name, link, type_of_data, type_of_objects, default_model, constant, created_at, status, view, tile_size, scale_factor)
            VALUES('satellite_building', 'satellite_building', array['satellite_images'], array['buildings'], false, false, '2024-06-01 00:00:01.000', 'Ready to use', 'yolov8', 640, 0.5);
            """
    )

    op.execute(
        """
            INSERT
            INTO ml(name, link, type_of_data, type_of_objects, default_model, constant, created_at, status, view, tile_size, scale_factor)
            VALUES('satellite_trees', 'satellite_trees', array['satellite_images'], array['trees'], false, false, '2024-06-01 00:00:01.000', 'Ready to use', 'yolov8', 640, 4.0);
            """
    )

    op.execute(
        """
            INSERT
            INTO ml(name, link, type_of_data, type_of_objects, default_model, constant, created_at, status, view, tile_size, scale_factor)
            VALUES('satellite_palm_tree', 'satellite_palm_tree', array['satellite_images'], array['palm_tree'], false, false, '2024-06-01 00:00:01.000', 'Ready to use', 'yolov8', 640, 1.0);
            """
    )

    op.execute(
        """
            INSERT
            INTO ml(name, link, type_of_data, type_of_objects, default_model, constant, created_at, status, view, tile_size, scale_factor)
            VALUES('satellite_farms', 'satellite_farms', array['satellite_images'], array['farms'], false, false, '2024-06-01 00:00:01.000', 'Ready to use', 'yolov8', 640, 0.25);
            """
    )


def downgrade() -> None:
    op.execute("DELETE FROM ml WHERE name='aerial_building'")
    op.execute("DELETE FROM ml WHERE name='aerial_trees'")
    op.execute("DELETE FROM ml WHERE name='aerial_palm_tree'")
    op.execute("DELETE FROM ml WHERE name='satellite_building'")
    op.execute("DELETE FROM ml WHERE name='satellite_trees'")
    op.execute("DELETE FROM ml WHERE name='satellite_palm_tree'")
    op.execute("DELETE FROM ml WHERE name='satellite_farms'")

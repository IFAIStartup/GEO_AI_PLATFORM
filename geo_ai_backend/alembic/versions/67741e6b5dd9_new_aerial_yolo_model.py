"""new_aerial_yolo_model

Revision ID: 67741e6b5dd9
Revises: c8970effcfe4
Create Date: 2024-07-03 11:53:14.440611

"""
import sqlalchemy as sa

from alembic import op



# revision identifiers, used by Alembic.
revision = '67741e6b5dd9'
down_revision = 'c8970effcfe4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
            INSERT
            INTO ml (name, link, type_of_data, type_of_objects, default_model, constant, created_at, status, view)
            VALUES ('yolov8x_aerial_base_02072024', 'yolov8x_aerial_base_02072024', array['aerial_images'], array['palm_tree', 'buildings', 'farms', 'trees'], True, False, '2024-06-01 00:00:01.000', 'Ready to use', 'yolov8');
        """
    )
    op.execute(
        """
            UPDATE ml
            SET default_model = False
            WHERE name = 'yolov8x_aerial_base';
        """
    )


def downgrade() -> None:
    op.execute(
        """
            UPDATE ml
            SET default_model = True
            WHERE name = 'yolov8x_aerial_base';
        """
    )
    op.execute("DELETE FROM ml WHERE name='yolov8x_aerial_base_02072024'")

"""new_model_garbage

Revision ID: 4688bb386ffc
Revises: 037228548b8a
Create Date: 2024-11-06 13:44:29.004858

"""
import sqlalchemy as sa

from alembic import op



# revision identifiers, used by Alembic.
revision = '4688bb386ffc'
down_revision = '037228548b8a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
            INSERT
            INTO ml(name, link, type_of_data, type_of_objects, default_model, constant, created_at, status, view, tile_size, scale_factor)
            VALUES('yolov8s_garbage_05112024', 'yolov8s_garbage_05112024', array['garbage'], array['household_garbage'], false, false, '2024-11-05 00:00:01.000', 'Ready to use', 'yolov8_det', 320, 1);
            """
    )


def downgrade() -> None:
    op.execute("DELETE FROM ml WHERE name='yolov8s_garbage_05112024'")

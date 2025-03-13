"""deleted_old_default_model_flag

Revision ID: 6626c298b0ac
Revises: 9119c61e12bb
Create Date: 2024-06-28 10:17:57.733243

"""
import sqlalchemy as sa

from alembic import op



# revision identifiers, used by Alembic.
revision = '6626c298b0ac'
down_revision = '9119c61e12bb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
            UPDATE ml
            SET default_model = False
            WHERE link = 'yolov8x_seg_aerial_1024_190823';
        """
    )
    op.execute(
        """
            UPDATE ml
            SET default_model = False
            WHERE link = 'satellite_yolov8l_18122023';
        """
    )


def downgrade() -> None:
    op.execute(
        """
            UPDATE ml
            SET default_model = True
            WHERE link = 'yolov8x_seg_aerial_1024_190823';
        """
    )
    op.execute(
        """
            UPDATE ml
            SET default_model = True
            WHERE link = 'satellite_yolov8l_18122023';
        """
    )

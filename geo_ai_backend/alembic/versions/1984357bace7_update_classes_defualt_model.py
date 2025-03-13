"""update_classes_defualt_model

Revision ID: 1984357bace7
Revises: 9d983461d5c6
Create Date: 2024-05-10 19:27:23.101827

"""
import sqlalchemy as sa

from alembic import op



# revision identifiers, used by Alembic.
revision = '1984357bace7'
down_revision = '9d983461d5c6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
            UPDATE ml
            SET type_of_objects = array['palm_tree', 'buildings', 'farms', 'trees']
            WHERE name = 'yolov8x_seg_aerial_1024_190823';
        """
    )
    op.execute(
        """
            UPDATE ml
            SET type_of_objects = array['roads', 'tracks']
            WHERE name = 'aerial_deeplabv3_plus_26012024';
        """
    )
    op.execute(
        """
            UPDATE ml
            SET type_of_objects = array['Lights pole', 'palm_tree', 'signboard', 'trees_group', 'trees_solo', 'traffic_sign']
            WHERE name = 'yolov8x_seg_360_1280_dataset_080123';
        """
    )
    op.execute(
        """
            UPDATE ml
            SET type_of_objects = array['building', 'roads']
            WHERE name = 'buildings360_r50_250923';
        """
    )
    op.execute(
        """
            UPDATE ml
            SET type_of_objects = array['palm_tree', 'buildings', 'farms', 'trees']
            WHERE name = 'satellite_yolov8l_18122023';
        """
    )
    op.execute(
        """
            UPDATE ml
            SET type_of_objects = array['roads', 'tracks']
            WHERE name = 'satellite_deeplab_260124';
        """
    )


def downgrade() -> None:
    op.execute(
        """
            UPDATE ml
            SET type_of_objects = array['palm_tree', 'buildings', 'farms', 'trees', 'roads']
            WHERE name = 'yolov8x_seg_aerial_1024_190823';
        """
    )
    op.execute(
        """
            UPDATE ml
            SET type_of_objects = array['palm_tree', 'buildings', 'farms', 'trees', 'roads', 'tracks']
            WHERE name = 'aerial_deeplabv3_plus_26012024';
        """
    )
    op.execute(
        """
            UPDATE ml
            SET type_of_objects = array['Lights pole', 'palm_tree', 'signboard', 'trees_group', 'trees_solo', 'traffic_sign', 'building', 'roads']
            WHERE name = 'yolov8x_seg_360_1280_dataset_080123';
        """
    )
    op.execute(
        """
            UPDATE ml
            SET type_of_objects = array['Lights pole', 'palm_tree', 'signboard', 'trees_group', 'trees_solo', 'traffic_sign', 'building', 'roads']
            WHERE name = 'buildings360_r50_250923';
        """
    )
    op.execute(
        """
            UPDATE ml
            SET type_of_objects = array['palm_tree', 'buildings', 'farms', 'trees', 'roads']
            WHERE name = 'satellite_yolov8l_18122023';
        """
    )
    op.execute(
        """
            UPDATE ml
            SET type_of_objects = array['palm_tree', 'buildings', 'farms', 'trees', 'roads', 'tracks']
            WHERE name = 'satellite_deeplab_260124';
        """
    )

"""upd_model

Revision ID: 752f9952ce2b
Revises: 768a759c36d3
Create Date: 2024-03-12 15:33:04.994931

"""
import sqlalchemy as sa

from alembic import op



# revision identifiers, used by Alembic.
revision = '752f9952ce2b'
down_revision = 'b32d4b575bb5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
            UPDATE ml
            SET name = 'aerial_deeplabv3_plus_26012024',
                link = 'aerial_deeplabv3_plus_26012024',
                type_of_objects = array['palm_tree', 'buildings', 'farms', 'trees', 'roads', 'tracks']
            WHERE name = 'r100_270923';
        """
    )
    op.execute(
        """
            UPDATE ml
            SET name = 'satellite_deeplab_260124',
                link = 'satellite_deeplab_260124',
                type_of_objects = array['palm_tree', 'buildings', 'farms', 'trees', 'roads', 'tracks']
            WHERE name = 'satellite_deeplabv3_plus_18122023';
        """
    )


def downgrade() -> None:
    op.execute(
        """
            UPDATE ml
            SET name = 'r100_270923',
                link = 'r100_270923',
                type_of_objects = array['palm_tree', 'buildings', 'farms', 'trees', 'roads']
            WHERE name = 'aerial_deeplabv3_plus_26012024';
        """
    )
    op.execute(
        """
            UPDATE ml
            SET name = 'satellite_deeplabv3_plus_18122023',
                link = 'satellite_deeplabv3_plus_18122023',
                type_of_objects = array['palm_tree', 'buildings', 'farms', 'trees', 'roads']
            WHERE name = 'satellite_deeplab_260124';
        """
    )

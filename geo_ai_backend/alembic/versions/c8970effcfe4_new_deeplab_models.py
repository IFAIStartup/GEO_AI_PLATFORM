"""new_deeplab_models

Revision ID: c8970effcfe4
Revises: 6626c298b0ac
Create Date: 2024-07-01 10:11:31.952697

"""
import sqlalchemy as sa

from alembic import op



# revision identifiers, used by Alembic.
revision = 'c8970effcfe4'
down_revision = '6626c298b0ac'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
            INSERT
            INTO ml (name, link, type_of_data, type_of_objects, default_model, constant, created_at, status, view)
            VALUES ('aerial_deeplabv3_plus_27062024', 'aerial_deeplabv3_plus_27062024', array['aerial_images'], array['roads', 'tracks'], True, False, '2024-05-15 00:00:01.000', 'Ready to use', 'deeplabv3');
        """
    )
    op.execute(
        """
            UPDATE ml
            SET default_model = False
            WHERE name = 'aerial_deeplabv3_plus_26012024';
        """
    )
    op.execute(
        """
            INSERT
            INTO ml (name, link, type_of_data, type_of_objects, default_model, constant, created_at, status, view)
            VALUES ('satellite_deeplabv3_plus_27062024', 'satellite_deeplabv3_plus_27062024', array['satellite_images'], array['roads', 'tracks'], True, False, '2024-05-15 00:00:01.000', 'Ready to use', 'deeplabv3');
        """
    )
    op.execute(
        """
            UPDATE ml
            SET default_model = False
            WHERE name = 'satellite_deeplab_260124';
        """
    )

def downgrade() -> None:
    op.execute(
        """
            DELETE FROM ml
            WHERE name = 'aerial_deeplabv3_plus_27062024';
        """
    )
    op.execute(
        """
            UPDATE ml
            SET default_model = True
            WHERE name = 'aerial_deeplabv3_plus_26012024';
        """
    )
    op.execute(
        """
            DELETE FROM ml
            WHERE name = 'satellite_deeplabv3_plus_27062024';
        """
    )
    op.execute(
        """
            UPDATE ml
            SET default_model = True
            WHERE name = 'satellite_deeplab_260124';
        """
    )

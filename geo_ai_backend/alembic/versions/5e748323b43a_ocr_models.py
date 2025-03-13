"""ocr_models

Revision ID: 5e748323b43a
Revises: 3b58ecd65f84
Create Date: 2024-12-10 11:44:04.078130

"""
import sqlalchemy as sa

from alembic import op



# revision identifiers, used by Alembic.
revision = '5e748323b43a'
down_revision = '3b58ecd65f84'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
            INSERT
            INTO ml (name, link, type_of_data, type_of_objects, default_model, constant, created_at, status, view)
            VALUES ('easyocr_detector', 'easyocr_detector', array['panorama_360'], array['signboard', 'traffic_sign'], True, True, '2024-07-18 00:00:01.000', 'Ready to use', 'panorama_360');
        """
    )
    op.execute(
        """
            INSERT
            INTO ml (name, link, type_of_data, type_of_objects, default_model, constant, created_at, status, view)
            VALUES ('easyocr_classifier_ar', 'easyocr_classifier_ar', array['panorama_360'], array['signboard', 'traffic_sign'], True, True, '2024-07-18 00:00:01.000', 'Ready to use', 'panorama_360');
        """
    )
    op.execute(
        """
            INSERT
            INTO ml (name, link, type_of_data, type_of_objects, default_model, constant, created_at, status, view)
            VALUES ('easyocr_classifier_en', 'easyocr_classifier_en', array['panorama_360'], array['signboard', 'traffic_sign'], True, True, '2024-07-18 00:00:01.000', 'Ready to use', 'panorama_360');
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM ml WHERE name='easyocr_detector'")
    op.execute("DELETE FROM ml WHERE name='easyocr_classifier_ar'")
    op.execute("DELETE FROM ml WHERE name='easyocr_classifier_en'")

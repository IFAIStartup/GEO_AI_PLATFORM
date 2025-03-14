"""fix const models

Revision ID: 63b7f386c297
Revises: f9ad2d9aaec7
Create Date: 2024-05-20 17:37:35.875413

"""
import sqlalchemy as sa

from alembic import op

from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '63b7f386c297'
down_revision = 'f9ad2d9aaec7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute(
        """
            UPDATE ml
            SET constant = False
            WHERE id = 4;
        """
    )
    op.execute(
        """
            UPDATE ml
            SET constant = False
            WHERE id = 6;
        """
    )
    op.execute(
        """
            UPDATE ml
            SET constant = False
            WHERE id = 7;
        """
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute(
        """
            UPDATE ml
            SET constant = True
            WHERE id = 4;
        """
    )
    op.execute(
        """
            UPDATE ml
            SET constant = True
            WHERE id = 6;
        """
    )
    op.execute(
        """
            UPDATE ml
            SET constant = True
            WHERE id = 7;
        """
    )
    # ### end Alembic commands ###

"""value_owner_id_error_history

Revision ID: 1f3ed97c1c3c
Revises: 6c147d157ea8
Create Date: 2024-12-06 14:06:19.975436

"""
import sqlalchemy as sa

from alembic import op



# revision identifiers, used by Alembic.
revision = '1f3ed97c1c3c'
down_revision = '6c147d157ea8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Вставка SQL запроса для обновления owner_id на основе соответствия created_by и username
    op.execute("""
            UPDATE error_history
            SET owner_id = (
                SELECT id
                FROM users
                WHERE users.username = error_history.username
                LIMIT 1
            )
            WHERE EXISTS (
                SELECT 1
                FROM users
                WHERE users.username = error_history.username
            );
        """)


def downgrade() -> None:
    # Если нужно отменить изменения, можно обнулить owner_id или вернуть его старое значение
    op.execute("UPDATE error_history SET owner_id = NULL;")

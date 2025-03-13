"""value_owner_id_action_history

Revision ID: 3b58ecd65f84
Revises: 1f3ed97c1c3c
Create Date: 2024-12-06 14:07:39.695395

"""
import sqlalchemy as sa

from alembic import op



# revision identifiers, used by Alembic.
revision = '3b58ecd65f84'
down_revision = '1f3ed97c1c3c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Вставка SQL запроса для обновления owner_id на основе соответствия created_by и username
    op.execute("""
            UPDATE action_history
            SET owner_id = (
                SELECT id
                FROM users
                WHERE users.username = action_history.username
                LIMIT 1
            )
            WHERE EXISTS (
                SELECT 1
                FROM users
                WHERE users.username = action_history.username
            );
        """)


def downgrade() -> None:
    # Если нужно отменить изменения, можно обнулить owner_id или вернуть его старое значение
    op.execute("UPDATE action_history SET owner_id = NULL;")

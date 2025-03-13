"""value_owner_id_projects

Revision ID: 6c147d157ea8
Revises: 6b9b514d0454
Create Date: 2024-12-06 14:01:47.234360

"""
import sqlalchemy as sa

from alembic import op



# revision identifiers, used by Alembic.
revision = '6c147d157ea8'
down_revision = '6b9b514d0454'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Вставка SQL запроса для обновления owner_id на основе соответствия created_by и username
    op.execute("""
           UPDATE projects
           SET owner_id = (
               SELECT id
               FROM users
               WHERE users.username = projects.created_by
               LIMIT 1
           )
           WHERE EXISTS (
               SELECT 1
               FROM users
               WHERE users.username = projects.created_by
           );
       """)


def downgrade() -> None:
    # Если нужно отменить изменения, можно обнулить owner_id или вернуть его старое значение
    op.execute("UPDATE projects SET owner_id = NULL;")

"""changed tupe columns

Revision ID: f50e70729410
Revises: f6c4e2da192c
Create Date: 2024-07-05 00:49:00.924468

"""
import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision = 'f50e70729410'
down_revision = 'f6c4e2da192c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'tmp_projects',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('ml_model_deeplab', sa.ARRAY(sa.String), nullable=True),
        sa.Column('ml_model', sa.ARRAY(sa.String), nullable=True)
    )
    op.execute(
        """
            INSERT INTO tmp_projects (id, ml_model_deeplab, ml_model)
            SELECT
                id,
                CASE
                    WHEN ml_model_deeplab = 'NULL' THEN NULL
                    ELSE ARRAY[ml_model_deeplab::varchar]
                END AS ml_model_deeplab,
                CASE
                    WHEN ml_model = 'NULL' THEN NULL
                    ELSE ARRAY[ml_model::varchar]
                END AS ml_model
            FROM public.projects;
        """
    )

    op.drop_column('projects', 'ml_model_deeplab')
    op.drop_column('projects', 'ml_model')
    op.add_column('projects', sa.Column('ml_model_deeplab', sa.ARRAY(sa.String()), nullable=True))
    op.add_column('projects', sa.Column('ml_model', sa.ARRAY(sa.String()), nullable=True))
    op.execute(
        """
            UPDATE public.projects p
            SET ml_model_deeplab = t.ml_model_deeplab,
                ml_model = t.ml_model
            FROM tmp_projects t
            WHERE p.id = t.id
        """
    )
    op.drop_table('tmp_projects')



def downgrade() -> None:
    op.create_table(
        'tmp_projects_old',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('ml_model_deeplab', sa.String(), nullable=True),
        sa.Column('ml_model', sa.String(), nullable=True)
    )
    op.execute(
        """
            INSERT INTO tmp_projects_old (id, ml_model_deeplab, ml_model)
            SELECT id,
                regexp_replace(ml_model_deeplab::text, '[{}"\\\\]', '', 'g') AS ml_model_deeplab,
                regexp_replace(ml_model::text, '[{}"\\\\]', '', 'g') AS ml_model
            FROM public.projects
        """
    )
    op.drop_column('projects', 'ml_model_deeplab')
    op.drop_column('projects', 'ml_model')
    op.add_column('projects', sa.Column('ml_model_deeplab', sa.String(), nullable=True))
    op.add_column('projects', sa.Column('ml_model', sa.String(), nullable=True))

    op.execute(
        """
            UPDATE public.projects p
            SET ml_model_deeplab = t.ml_model_deeplab,
                ml_model = t.ml_model
            FROM tmp_projects_old t
            WHERE p.id = t.id
        """
    )
    op.drop_table('tmp_projects_old')

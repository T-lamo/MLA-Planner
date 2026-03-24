"""add_template_role_membres

Revision ID: f15f3d7ac637
Revises: 54f4e7390542
Create Date: 2026-03-23 23:59:45.923750

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f15f3d7ac637'
down_revision: Union[str, Sequence[str], None] = '54f4e7390542'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crée t_planning_template_role_membre si elle n'existe pas encore."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 't_planning_template_role_membre' not in inspector.get_table_names():
        op.create_table(
            't_planning_template_role_membre',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('template_role_id', sa.String(), nullable=False),
            sa.Column('membre_id', sa.String(), nullable=False),
            sa.ForeignKeyConstraint(
                ['membre_id'],
                ['t_membre.id'],
                ondelete='CASCADE',
            ),
            sa.ForeignKeyConstraint(
                ['template_role_id'],
                ['t_planningtemplaterole.id'],
                ondelete='CASCADE',
            ),
            sa.PrimaryKeyConstraint('id'),
        )


def downgrade() -> None:
    """Supprime t_planning_template_role_membre."""
    op.drop_table('t_planning_template_role_membre')

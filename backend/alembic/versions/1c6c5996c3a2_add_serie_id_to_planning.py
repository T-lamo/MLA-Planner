"""add_serie_id_to_planning

Revision ID: 1c6c5996c3a2
Revises: f15f3d7ac637
Create Date: 2026-03-24 17:06:31.393428

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '1c6c5996c3a2'
down_revision: Union[str, Sequence[str], None] = 'f15f3d7ac637'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Note: les drop_index/drop_table sur t_organisationicc ont été retirés car
    # b2c3d4e5f6a7 a déjà renommé la table en t_organisation (toujours utilisée).
    # Ces opérations étaient des résidus d'auto-génération incorrects.
    op.add_column('t_planningservice', sa.Column('serie_id', sa.String(), nullable=True))
    op.create_index(op.f('ix_t_planningservice_serie_id'), 't_planningservice', ['serie_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_t_planningservice_serie_id'), table_name='t_planningservice')
    op.drop_column('t_planningservice', 'serie_id')

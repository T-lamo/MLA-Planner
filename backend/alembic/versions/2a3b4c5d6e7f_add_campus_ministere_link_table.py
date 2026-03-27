"""add_campus_ministere_link_table

Revision ID: 2a3b4c5d6e7f
Revises: 1c6c5996c3a2
Create Date: 2026-03-26 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '2a3b4c5d6e7f'
down_revision: Union[str, Sequence[str], None] = 'b3c4d5e6f7a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        't_campus_ministere_link',
        sa.Column('campus_id', sa.String(), nullable=False),
        sa.Column('ministere_id', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['campus_id'], ['t_campus.id']),
        sa.ForeignKeyConstraint(['ministere_id'], ['t_ministere.id']),
        sa.PrimaryKeyConstraint('campus_id', 'ministere_id'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('t_campus_ministere_link')

"""add_template_id_to_planningservice

Revision ID: 6dbf6e801432
Revises: 284f2e637ec8
Create Date: 2026-03-21 20:54:12.221169

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6dbf6e801432'
down_revision: Union[str, Sequence[str], None] = '284f2e637ec8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        't_planningservice',
        sa.Column('template_id', sa.String(), nullable=True),
    )
    op.create_foreign_key(
        'fk_planningservice_template_id',
        't_planningservice',
        't_planningtemplate',
        ['template_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        'fk_planningservice_template_id',
        't_planningservice',
        type_='foreignkey',
    )
    op.drop_column('t_planningservice', 'template_id')

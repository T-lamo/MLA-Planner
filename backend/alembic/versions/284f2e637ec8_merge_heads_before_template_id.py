"""merge_heads_before_template_id

Revision ID: 284f2e637ec8
Revises: 247298ef89ca, d0e1f2a3b4c5
Create Date: 2026-03-21 20:53:49.045478

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '284f2e637ec8'
down_revision: Union[str, Sequence[str], None] = ('247298ef89ca', 'd0e1f2a3b4c5')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

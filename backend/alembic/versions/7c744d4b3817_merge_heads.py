"""merge_heads

Revision ID: 7c744d4b3817
Revises: b2c3d4e5f6a7, c1d2e3f4a5b6
Create Date: 2026-03-16 00:15:53.417872

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c744d4b3817'
down_revision: Union[str, Sequence[str], None] = ('b2c3d4e5f6a7', 'c1d2e3f4a5b6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

"""merge_heads

Revision ID: 2b5bcd571c91
Revises: 8b92d08a7514, a1b2c3d4e5f6
Create Date: 2026-03-21 19:34:30.364242

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2b5bcd571c91'
down_revision: Union[str, Sequence[str], None] = ('8b92d08a7514', 'a1b2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

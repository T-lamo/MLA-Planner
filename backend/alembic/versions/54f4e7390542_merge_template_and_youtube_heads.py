"""merge_template_and_youtube_heads

Revision ID: 54f4e7390542
Revises: 6dbf6e801432, e1f2a3b4c5d6
Create Date: 2026-03-21 23:22:13.295231

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '54f4e7390542'
down_revision: Union[str, Sequence[str], None] = ('6dbf6e801432', 'e1f2a3b4c5d6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

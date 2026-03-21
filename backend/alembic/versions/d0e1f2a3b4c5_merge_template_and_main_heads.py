"""merge_template_and_main_heads

Revision ID: d0e1f2a3b4c5
Revises: 7c744d4b3817, 26a24c081bf1
Create Date: 2026-03-21 20:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "d0e1f2a3b4c5"
down_revision: Union[str, Sequence[str], None] = (
    "7c744d4b3817",
    "26a24c081bf1",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge: planning-templates branch + main branch."""
    pass


def downgrade() -> None:
    """Downgrade merge."""
    pass

"""add_visibilite_to_planning_template

Revision ID: b3c4d5e6f7a8
Revises: 1c6c5996c3a2
Create Date: 2026-03-24 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b3c4d5e6f7a8"
down_revision: Union[str, None] = "1c6c5996c3a2"
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "t_planningtemplate",
        sa.Column(
            "visibilite",
            sa.String(20),
            nullable=False,
            server_default="MINISTERE",
        ),
    )


def downgrade() -> None:
    op.drop_column("t_planningtemplate", "visibilite")

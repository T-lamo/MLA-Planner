"""add ministere_id to t_affectation

Revision ID: a8c3f5d2e1b7
Revises: f3a1b2c9d0e4
Create Date: 2026-03-13 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a8c3f5d2e1b7"
down_revision: Union[str, Sequence[str], None] = "7539d6731033"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add ministere_id column to t_affectation with FK to t_ministere."""
    op.add_column(
        "t_affectation",
        sa.Column("ministere_id", sa.String(), nullable=True),
    )
    op.create_foreign_key(
        "fk_affectation_ministere",
        "t_affectation",
        "t_ministere",
        ["ministere_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Remove ministere_id column from t_affectation."""
    op.drop_constraint(
        "fk_affectation_ministere", "t_affectation", type_="foreignkey"
    )
    op.drop_column("t_affectation", "ministere_id")

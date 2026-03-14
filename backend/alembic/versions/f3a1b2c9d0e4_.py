"""add campus_principal_id to t_membre

Revision ID: f3a1b2c9d0e4
Revises: 2de1716fa833
Create Date: 2026-03-06 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f3a1b2c9d0e4"
down_revision: Union[str, Sequence[str], None] = "2de1716fa833"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add campus_principal_id column to t_membre with FK to t_campus."""
    op.add_column(
        "t_membre",
        sa.Column("campus_principal_id", sa.String(), nullable=True),
    )
    op.create_foreign_key(
        "fk_membre_campus_principal",
        "t_membre",
        "t_campus",
        ["campus_principal_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Remove campus_principal_id column from t_membre."""
    op.drop_constraint(
        "fk_membre_campus_principal", "t_membre", type_="foreignkey"
    )
    op.drop_column("t_membre", "campus_principal_id")

"""add ministere_id to t_indisponibilite

Revision ID: c1d2e3f4a5b6
Revises: 9a3b08e0c005
Create Date: 2026-03-15 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, None] = "9a3b08e0c005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "t_indisponibilite",
        sa.Column(
            "ministere_id",
            sa.String(),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_indisponibilite_ministere",
        "t_indisponibilite",
        "t_ministere",
        ["ministere_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_indisponibilite_ministere_id",
        "t_indisponibilite",
        ["ministere_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_indisponibilite_ministere_id",
        table_name="t_indisponibilite",
    )
    op.drop_constraint(
        "fk_indisponibilite_ministere",
        "t_indisponibilite",
        type_="foreignkey",
    )
    op.drop_column("t_indisponibilite", "ministere_id")

"""rc158_catalogue_global_roles

Revision ID: d1e2f3a4b5c6
Revises: 2a3b4c5d6e7f, b1c2d3e4f5a6, e5f6a7b8c9d0
Create Date: 2026-03-29 00:00:00.000000

RC-158 : Passer CategorieRole/RoleCompetence en catalogue global.

Changements :
  - Supprime la colonne ministere_id de t_categorierole
    (CategorieRole devient un catalogue global)
  - Crée t_ministere_role_config (ministere_id PK FK, role_code PK FK)
    comme table de liaison N:N entre Ministere et RoleCompetence
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, Sequence[str], None] = (
    "2a3b4c5d6e7f",
    "b1c2d3e4f5a6",
    "e5f6a7b8c9d0",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Supprimer la FK et la colonne ministere_id de t_categorierole
    op.drop_constraint(
        "t_categorierole_ministere_id_fkey",
        "t_categorierole",
        type_="foreignkey",
    )
    op.drop_column("t_categorierole", "ministere_id")

    # 2. Créer la table t_ministere_role_config
    op.create_table(
        "t_ministere_role_config",
        sa.Column(
            "ministere_id",
            sa.String(),
            nullable=False,
        ),
        sa.Column(
            "role_code",
            sa.String(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["ministere_id"],
            ["t_ministere.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["role_code"],
            ["t_rolecompetence.code"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("ministere_id", "role_code"),
    )


def downgrade() -> None:
    # 1. Supprimer t_ministere_role_config
    op.drop_table("t_ministere_role_config")

    # 2. Remettre ministere_id sur t_categorierole
    op.add_column(
        "t_categorierole",
        sa.Column(
            "ministere_id",
            sa.String(),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "t_categorierole_ministere_id_fkey",
        "t_categorierole",
        "t_ministere",
        ["ministere_id"],
        ["id"],
        ondelete="SET NULL",
    )

"""add songbook tables (chant, categorie, contenu, artiste_link, tag)

Revision ID: a1b2c3d4e5f6
Revises: f3a1b2c9d0e4
Create Date: 2026-03-20 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "f3a1b2c9d0e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crée les 5 tables du module Songbook + index."""
    op.create_table(
        "t_chant_categorie",
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("libelle", sa.String(length=100), nullable=False),
        sa.Column("ordre", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("code"),
    )

    op.create_table(
        "t_chant",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("titre", sa.String(length=200), nullable=False),
        sa.Column("artiste", sa.String(length=150), nullable=True),
        sa.Column("campus_id", sa.String(), nullable=False),
        sa.Column("categorie_code", sa.String(length=30), nullable=True),
        sa.Column("actif", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "date_creation",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["campus_id"], ["t_campus.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["categorie_code"],
            ["t_chant_categorie.code"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "t_chant_contenu",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("chant_id", sa.String(), nullable=False),
        sa.Column("tonalite", sa.String(length=10), nullable=False),
        sa.Column("paroles_chords", sa.Text(), nullable=False),
        sa.Column(
            "version", sa.Integer(), nullable=False, server_default="1"
        ),
        sa.Column(
            "date_modification",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["chant_id"], ["t_chant.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chant_id", name="uq_chant_contenu_chant_id"),
    )

    op.create_table(
        "t_chant_artiste_link",
        sa.Column("chant_id", sa.String(), nullable=False),
        sa.Column("artiste_nom", sa.String(length=150), nullable=False),
        sa.Column(
            "role",
            sa.String(length=50),
            nullable=False,
            server_default="INTERPRETE",
        ),
        sa.ForeignKeyConstraint(
            ["chant_id"], ["t_chant.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("chant_id", "artiste_nom"),
    )

    op.create_table(
        "t_chant_tag",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("chant_id", sa.String(), nullable=False),
        sa.Column("libelle", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(
            ["chant_id"], ["t_chant.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Index 1 — filtre multi-tenant (campus_id)
    op.create_index(
        "idx_chant_campus_id", "t_chant", ["campus_id"]
    )
    # Index 2 — tri artiste NULLS LAST (PostgreSQL)
    op.execute(
        "CREATE INDEX idx_chant_artiste ON t_chant "
        "(artiste NULLS LAST, titre)"
    )
    # Index 3 — groupement par catégorie
    op.create_index(
        "idx_chant_categorie_code", "t_chant", ["categorie_code"]
    )


def downgrade() -> None:
    """Supprime les tables et index du module Songbook."""
    op.drop_index("idx_chant_categorie_code", table_name="t_chant")
    op.execute("DROP INDEX IF EXISTS idx_chant_artiste")
    op.drop_index("idx_chant_campus_id", table_name="t_chant")
    op.drop_table("t_chant_tag")
    op.drop_table("t_chant_artiste_link")
    op.drop_table("t_chant_contenu")
    op.drop_table("t_chant")
    op.drop_table("t_chant_categorie")

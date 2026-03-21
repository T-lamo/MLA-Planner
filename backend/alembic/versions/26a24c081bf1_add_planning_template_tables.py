"""add_planning_template_tables

Revision ID: 26a24c081bf1
Revises: 2b5bcd571c91
Create Date: 2026-03-21 19:34:41.155894

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "26a24c081bf1"
down_revision: Union[str, Sequence[str], None] = "2b5bcd571c91"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crée les tables des templates de planning."""
    op.create_table(
        "t_planningtemplate",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("nom", sa.String(length=150), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("activite_type", sa.String(length=100), nullable=False),
        sa.Column("duree_minutes", sa.Integer(), nullable=False),
        sa.Column("campus_id", sa.String(), nullable=False),
        sa.Column("ministere_id", sa.String(), nullable=False),
        sa.Column("created_by_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("used_count", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["campus_id"],
            ["t_campus.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["t_membre.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["ministere_id"],
            ["t_ministere.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "t_planningtemplateslot",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("template_id", sa.String(), nullable=False),
        sa.Column("nom_creneau", sa.String(length=100), nullable=False),
        sa.Column("offset_debut_minutes", sa.Integer(), nullable=False),
        sa.Column("offset_fin_minutes", sa.Integer(), nullable=False),
        sa.Column("nb_personnes_requis", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["template_id"],
            ["t_planningtemplate.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "t_planningtemplaterole",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("slot_id", sa.String(), nullable=False),
        sa.Column("role_code", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(
            ["slot_id"],
            ["t_planningtemplateslot.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Supprime les tables des templates de planning."""
    op.drop_table("t_planningtemplaterole")
    op.drop_table("t_planningtemplateslot")
    op.drop_table("t_planningtemplate")

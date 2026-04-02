"""add_planning_chant_link

Revision ID: b1c2d3e4f5a6
Revises: a1b2c3d4e5f6
Create Date: 2026-03-27 00:01:00.000000

Crée la table de liaison t_planning_chant_link (planning ↔ chant ordonné).
"""

from alembic import op
import sqlalchemy as sa

revision = "b1c2d3e4f5a6"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "t_planning_chant_link",
        sa.Column("planning_id", sa.String(), nullable=False),
        sa.Column("chant_id", sa.String(), nullable=False),
        sa.Column("ordre", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(
            ["planning_id"],
            ["t_planningservice.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["chant_id"],
            ["t_chant.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("planning_id", "chant_id"),
    )
    op.create_index(
        "ix_planning_chant_link_planning_id",
        "t_planning_chant_link",
        ["planning_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_planning_chant_link_planning_id",
        table_name="t_planning_chant_link",
    )
    op.drop_table("t_planning_chant_link")

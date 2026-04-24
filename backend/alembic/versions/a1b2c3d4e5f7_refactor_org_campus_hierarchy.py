"""refactor_org_campus_hierarchy

Remove Pays table. Add parent_id to Organisation (self-ref hierarchy).
Replace pays_id with organisation_id on Campus. Add pays varchar to Campus.

Revision ID: a1b2c3d4e5f7
Revises: d1e2f3a4b5c6
Create Date: 2026-04-04 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "a1b2c3d4e5f7"
down_revision = "d1e2f3a4b5c6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add parent_id to t_organisation (nullable self-ref FK)
    op.add_column(
        "t_organisation",
        sa.Column("parent_id", sa.String(length=36), nullable=True),
    )
    op.create_foreign_key(
        "fk_organisation_parent_id",
        "t_organisation",
        "t_organisation",
        ["parent_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # 2. Add organisation_id (nullable) and pays varchar to t_campus
    op.add_column(
        "t_campus",
        sa.Column("organisation_id", sa.String(length=36), nullable=True),
    )
    op.add_column(
        "t_campus",
        sa.Column("pays", sa.String(length=100), nullable=True, server_default="France"),
    )

    # 3. Migrate campus data: resolve pays_id → organisation_id via t_pays
    op.execute(
        """
        UPDATE t_campus c
        SET organisation_id = p.organisation_id
        FROM t_pays p
        WHERE c.pays_id = p.id
          AND p.organisation_id IS NOT NULL
        """
    )

    # 4. Set pays string from t_pays nom
    op.execute(
        """
        UPDATE t_campus c
        SET pays = p.nom
        FROM t_pays p
        WHERE c.pays_id = p.id
        """
    )

    # 5. Make organisation_id NOT NULL (all rows should be populated)
    op.alter_column("t_campus", "organisation_id", nullable=False)

    # 6. Create FK from t_campus.organisation_id → t_organisation.id
    op.create_foreign_key(
        "fk_campus_organisation_id",
        "t_campus",
        "t_organisation",
        ["organisation_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 7. Drop t_campus.pays_id FK and column
    op.drop_constraint("t_campus_pays_id_fkey", "t_campus", type_="foreignkey")
    op.drop_column("t_campus", "pays_id")

    # 8. Drop t_pays table (no more dependents)
    op.drop_table("t_pays")


def downgrade() -> None:
    # Recreate t_pays
    op.create_table(
        "t_pays",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("nom", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=10), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("organisation_id", sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(
            ["organisation_id"], ["t_organisation.id"], ondelete="SET NULL"
        ),
    )

    # Restore pays_id on t_campus
    op.add_column(
        "t_campus",
        sa.Column("pays_id", sa.String(length=36), nullable=True),
    )

    # Drop new columns/constraints
    op.drop_constraint("fk_campus_organisation_id", "t_campus", type_="foreignkey")
    op.drop_column("t_campus", "organisation_id")
    op.drop_column("t_campus", "pays")

    # Drop organisation self-ref
    op.drop_constraint("fk_organisation_parent_id", "t_organisation", type_="foreignkey")
    op.drop_column("t_organisation", "parent_id")

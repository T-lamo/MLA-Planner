"""rename t_organisationicc to t_organisation

Revision ID: b2c3d4e5f6a7
Revises: 9a3b08e0c005, 7539d6731033
Create Date: 2026-03-15 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op

revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, tuple, None] = ('9a3b08e0c005', '7539d6731033')
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table('t_organisationicc', 't_organisation')
    op.execute(
        "ALTER INDEX IF EXISTS ix_t_organisationicc_nom "
        "RENAME TO ix_t_organisation_nom"
    )
    op.execute(
        "ALTER INDEX IF EXISTS ix_t_organisationicc_deleted_at "
        "RENAME TO ix_t_organisation_deleted_at"
    )


def downgrade() -> None:
    op.rename_table('t_organisation', 't_organisationicc')
    op.execute(
        "ALTER INDEX IF EXISTS ix_t_organisation_nom "
        "RENAME TO ix_t_organisationicc_nom"
    )
    op.execute(
        "ALTER INDEX IF EXISTS ix_t_organisation_deleted_at "
        "RENAME TO ix_t_organisationicc_deleted_at"
    )

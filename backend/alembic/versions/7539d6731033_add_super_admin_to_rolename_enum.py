"""add_super_admin_to_rolename_enum

Revision ID: 7539d6731033
Revises: b5e4e657bc15
Create Date: 2026-03-06 23:54:01.804373

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7539d6731033'
down_revision: Union[str, Sequence[str], None] = 'b5e4e657bc15'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Ajoute 'Super Admin' au type enum rolename."""
    op.execute("ALTER TYPE rolename ADD VALUE IF NOT EXISTS 'SUPER_ADMIN' BEFORE 'ADMIN'")


def downgrade() -> None:
    """PostgreSQL ne supporte pas la suppression d'une valeur d'enum nativement."""
    pass

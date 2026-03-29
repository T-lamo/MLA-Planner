"""role_libelle_varchar

Revision ID: e5f6a7b8c9d0
Revises: f3a1b2c9d0e4
Create Date: 2026-03-27 00:00:00.000000

Convertit t_role.libelle du type PG enum 'rolename' vers VARCHAR(100).
Préserve toutes les données existantes via USING libelle::text.
"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "f3a1b2c9d0e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_DROP_UNIQUE_SQL = """
DO $$
DECLARE r RECORD;
BEGIN
    FOR r IN
        SELECT conname FROM pg_constraint
        WHERE conrelid = 't_role'::regclass
          AND contype = 'u'
          AND conkey @> ARRAY[
              (SELECT attnum FROM pg_attribute
               WHERE attrelid = 't_role'::regclass AND attname = 'libelle')
          ]::smallint[]
    LOOP
        EXECUTE 'ALTER TABLE t_role DROP CONSTRAINT ' || quote_ident(r.conname);
    END LOOP;
END $$;
"""


def upgrade() -> None:
    # Supprimer toutes les contraintes UNIQUE sur libelle (il peut y en avoir 2)
    op.execute(_DROP_UNIQUE_SQL)

    # Convertir la colonne enum → VARCHAR(100) en préservant les données
    op.execute(
        "ALTER TABLE t_role "
        "ALTER COLUMN libelle TYPE VARCHAR(100) USING libelle::text"
    )

    # Supprimer le type PG enum 'rolename' devenu inutile
    op.execute("DROP TYPE IF EXISTS rolename")

    # Recréer une seule contrainte UNIQUE
    op.create_unique_constraint("t_role_libelle_key", "t_role", ["libelle"])


def downgrade() -> None:
    # Recréer le type enum PG avec les 4 valeurs d'origine
    op.execute(
        "CREATE TYPE rolename AS ENUM "
        "('Super Admin', 'Admin', 'Responsable MLA', 'Membre MLA')"
    )

    op.drop_constraint("t_role_libelle_key", "t_role", type_="unique")

    op.execute(
        "ALTER TABLE t_role "
        "ALTER COLUMN libelle TYPE rolename USING libelle::rolename"
    )

    op.create_unique_constraint("t_role_libelle_key", "t_role", ["libelle"])

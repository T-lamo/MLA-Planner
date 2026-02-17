# backend/alembic/env.py
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

# 1. GESTION DYNAMIQUE DU PYTHONPATH
# On remonte d'un cran pour inclure le dossier 'backend' et 'src' dans le path Python
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

# 2. IMPORT DES SETTINGS ET DES MODÈLES
# On utilise les chemins basés sur 'src' comme racine
from src.core.settings import settings
import src.models.schema_db_model as schema

# --- FORCE L'ENREGISTREMENT DES TABLES ---
# Important : SQLModel a besoin que les classes soient importées pour remplir 
# SQLModel.metadata. On boucle sur le __all__ défini dans ton fichier de modèles.
if hasattr(schema, "__all__"):
    for export_name in schema.__all__:
        # Cela force l'évaluation de la classe et son enregistrement dans le registre
        getattr(schema, export_name)

# 3. CONFIGURATION DES MÉTADONNÉES
# On pointe vers le registre global de SQLModel qui contient maintenant toutes tes tables
target_metadata = SQLModel.metadata

# Config d'Alembic
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def run_migrations_offline() -> None:
    """Exécution des migrations en mode 'offline' (génération de SQL)."""
    url = settings.sync_database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "pyformat"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Exécution des migrations en mode 'online' (connexion directe à la DB)."""
    
    # On récupère la configuration et on injecte l'URL de la base depuis les settings
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = settings.sync_database_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            # compare_type=True permet de détecter si tu changes le type d'une colonne
            compare_type=True,
            # Indispensable si tu as plusieurs schémas ou des tables existantes
            include_schemas=True 
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
from core.settings import settings
from sqlalchemy import text  # Import nécessaire
from sqlmodel import Session, SQLModel, StaticPool, create_engine


class Database:
    _engine = None

    @classmethod
    def get_engine(cls):
        if cls._engine is None:
            url = settings.sync_database_url

            # Configuration spécifique au moteur (Engine-specific)
            # On ne vérifie pas "si on teste", mais "si le moteur est SQLite"
            connect_args = {}
            poolclass = None

            if url.startswith("sqlite"):
                connect_args = {"check_same_thread": False}
                poolclass = StaticPool

            cls._engine = create_engine(
                url, connect_args=connect_args, poolclass=poolclass, echo=True
            )
        return cls._engine

    @classmethod
    def get_session(cls):
        engine = cls.get_engine()
        with Session(engine) as session:
            yield session

    @classmethod
    def get_db_for_route(cls):
        """Gère le cycle de vie de la session (commit/rollback) pour les routes."""
        engine = cls.get_engine()
        with Session(engine) as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()

    @classmethod
    def init_db(cls):
        # pylint: disable=import-outside-toplevel
        # pylint: disable=unused-import
        from models import __all__ as models  # noqa: F401

        engine = cls.get_engine()
        SQLModel.metadata.create_all(engine)

    @classmethod
    def _recreate_db(cls):
        """
        ⚠️ DANGEREUX – Supprime et recrée tout le schéma public proprement
        """
        engine = cls.get_engine()

        with engine.connect() as connection:
            with connection.begin():
                # On force la suppression du schéma public et on le recrée
                # C'est la méthode la plus fiable pour nettoyer un Postgres
                connection.execute(text("DROP SCHEMA public CASCADE;"))
                connection.execute(text("CREATE SCHEMA public;"))
                # On s'assure que les permissions sont correctes
                connection.execute(text("GRANT ALL ON SCHEMA public TO public;"))

        # On recrée tout via SQLModel
        SQLModel.metadata.create_all(engine)

    @classmethod
    def disconnect(cls):
        if cls._engine:
            cls._engine.dispose()
            cls._engine = None

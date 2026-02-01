from sqlalchemy import text  # Import nécessaire
from sqlmodel import Session, SQLModel, create_engine

from core.settings import settings


class Database:
    _engine = None

    @classmethod
    def get_engine(cls):
        if cls._engine is None:
            cls._engine = create_engine(
                f"postgresql+psycopg2://{settings.DB_USER}:{settings.DB_PASSWORD}"
                f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}",
                echo=True,
            )
        return cls._engine

    @classmethod
    def get_session(cls):
        engine = cls.get_engine()
        with Session(engine) as session:
            yield session

    @classmethod
    def init_db(cls):
        # pylint: disable=import-outside-toplevel
        from models import __all__ as models  # pylint: disable=unused-import

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

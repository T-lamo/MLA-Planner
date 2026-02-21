import os
from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# ENV par défaut = dev (Render injectera ENV=production)
ENV = os.getenv("ENV", "dev")

dotenv_path = f".env.{ENV}"
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)


class Settings(BaseSettings):
    # Environment
    ENV: str = "dev"

    # Database Defaults (utilisés en local si DATABASE_URL est vide)
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432  # Port standard Postgres
    DB_NAME: str = "mla_planning_db"

    # Cette variable sera remplie par Render via l'onglet Environment
    DATABASE_URL: Optional[str] = None

    # JWT
    JWT_SECRET_KEY: str = "votre_cle_secrete_super_longue"  # À définir sur Render aussi
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = {
        "extra": "allow",
        "case_sensitive": True,
    }

    @property
    def sync_database_url(self) -> str:
        """
        Gère la connexion à PostgreSQL de manière robuste.
        """
        # 1. Si Render injecte DATABASE_URL
        if self.DATABASE_URL:
            if self.DATABASE_URL.startswith("postgres://"):
                return self.DATABASE_URL.replace(
                    "postgres://", "postgresql+psycopg2://", 1
                )
            if self.DATABASE_URL.startswith("postgresql://"):
                return self.DATABASE_URL.replace(
                    "postgresql://", "postgresql+psycopg2://", 1
                )
            return self.DATABASE_URL

        # 2. Sinon, construction manuelle pour le local
        return (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


# Instance globale
settings: Settings = Settings()

import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# --------------------------
# Charger le .env si disponible
# --------------------------
# ENV par défaut = dev
ENV = os.getenv("ENV", "dev")

# Charger .env.<ENV> seulement si le fichier existe
dotenv_path = f".env.{ENV}"
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# --------------------------
# Settings Pydantic
# --------------------------
class Settings(BaseSettings):
    # Environment
    ENV: str = "dev"

    # Database
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "mla_planning_db"

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Pydantic v2 config
    model_config = {
        "extra": "allow",
        "case_sensitive": True,
    }

# Instance globale
settings = Settings()

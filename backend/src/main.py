import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # Import indispensable

from conf.db.database import Database
from core.exceptions.exceptions_handlers import register_exception_handlers
from core.settings import settings
from routes import router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Initialisation de la base de données au démarrage
    if settings.ENV != "production":
        Database.init_db()
    yield
    Database.disconnect()


# Configuration de l'application
app = FastAPI(
    title="MLA Planning API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if settings.ENV == "prod" else "/docs",
    redoc_url=None if settings.ENV == "prod" else "/redoc",
)

# --- CONFIGURATION CORS ---
# On récupère les origines depuis les settings ou l'environnement
# Si ALLOWED_ORIGINS n'existe pas, on autorise localhost par défaut
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],  # Autorise GET, POST, PUT, DELETE, etc.
    allow_headers=[
        "*"
    ],  # Autorise tous les headers (Content-Type, Authorization, etc.)
)
# ---------------------------

app.include_router(router)
register_exception_handlers(app)

if __name__ == "__main__":
    # Note : uvicorn.run utilise 8000 ici, mais Render utilisera $PORT via le Dockerfile
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

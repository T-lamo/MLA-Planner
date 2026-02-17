from contextlib import asynccontextmanager

import uvicorn
from conf.db.database import Database
from core.exceptions.exceptions_handlers import register_exception_handlers

# from core import register_exception_handlers
from core.settings import settings
from fastapi import FastAPI
from routes import router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Initialisation de la base de données au démarrage de l'application
    Database.init_db()

    yield
    Database.disconnect()


# Deactivate docs in production
app = FastAPI(
    title="MLA Planning API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if settings.ENV == "prod" else "/docs",
    redoc_url=None if settings.ENV == "prod" else "/redoc",
)

app.include_router(router)
register_exception_handlers(app)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

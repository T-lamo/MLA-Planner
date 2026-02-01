from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from sqlmodel import Session

from conf.db.database import Database
from conf.db.seed.seed_service import SeedService

# from core import register_exception_handlers
from core.settings import settings
from routes import router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Initialisation de la base de données au démarrage de l'application
    Database.init_db()
    with Session(Database.get_engine()) as session:
        SeedService(session).run()
    yield
    Database.disconnect()


# Deactivate docs in production
app = FastAPI(
    title="DigiChees API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if settings.ENV == "prod" else "/docs",
    redoc_url=None if settings.ENV == "prod" else "/redoc",
)

app.include_router(router)
# register_exception_handlers(app)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}

# src/core/exception_handlers.py
import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.datastructures import FormData
from starlette.status import HTTP_422_UNPROCESSABLE_CONTENT

from core.exceptions.app_exception import AppException
from core.settings import settings

logger = logging.getLogger(__name__)


def _serialize_errors(errors: list[dict]) -> list[dict]:
    """Rend les erreurs Pydantic v2 sérialisables en JSON.

    Pydantic v2 peut placer des objets Exception dans ctx['error'] —
    on les convertit en str pour éviter une TypeError lors de JSONResponse.
    """
    result = []
    for err in errors:
        safe: dict = {k: v for k, v in err.items() if k != "ctx"}
        if "ctx" in err:
            safe["ctx"] = {k: str(v) for k, v in err["ctx"].items()}
        result.append(safe)
    return result


def register_exception_handlers(app):
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request,
        exc: RequestValidationError,
    ):
        raw_body = exc.body
        formatted_body = raw_body

        # Si le body est un objet FormData,
        # on le convertit en dictionnaire
        if isinstance(raw_body, FormData):
            formatted_body = dict(raw_body)
        return JSONResponse(
            status_code=HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "error": "ValidationError",
                "detail": _serialize_errors(list(exc.errors())),
                "body": formatted_body,
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        _request: Request,
        exc: Exception,
    ):
        logger.exception("Unhandled exception: %s", exc)
        detail = (
            str(exc) if settings.ENV != "prod" else "Une erreur interne est survenue."
        )
        return JSONResponse(
            status_code=500,
            content={"error": "InternalServerError", "detail": detail},
        )

    @app.exception_handler(AppException)
    async def app_exception_handler(_request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.http_status,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "status": exc.http_status,
                }
            },
        )


__all__ = ["register_exception_handlers"]

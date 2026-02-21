# src/core/exception_handlers.py
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.datastructures import FormData
from starlette.status import HTTP_422_UNPROCESSABLE_CONTENT

from core.exceptions.app_exception import AppException


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
                "detail": exc.errors(),
                "body": formatted_body,
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        _request: Request,
        exc: Exception,
    ):
        # Log the exception details here
        print(f"Exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={"error": "InternalServerError", "detail": str(exc)},
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

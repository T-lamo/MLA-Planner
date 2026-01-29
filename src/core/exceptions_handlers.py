# src/core/exception_handlers.py
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_CONTENT


def register_exception_handlers(app):
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        # request: Request,
        exc: RequestValidationError,
    ):
        return JSONResponse(
            status_code=HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "error": "ValidationError",
                "detail": exc.errors(),
                "body": exc.body,
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        # request: Request,
        exc: Exception,
    ):
        # Log the exception details here
        print(f"Exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={"error": "InternalServerError", "detail": str(exc)},
        )


__all__ = ["register_exception_handlers"]

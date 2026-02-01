# src/core/exceptions.py
from fastapi import HTTPException, status


class NotFoundException(HTTPException):
    def __init__(self, detail: str = "Ressource introuvable"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class BadRequestException(HTTPException):
    def __init__(self, detail: str = "Requête invalide"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class UnauthorizedException(HTTPException):
    def __init__(self, detail: str = "Non autorisé"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class ForbiddenException(HTTPException):
    def __init__(self, detail: str = "Non autorisé"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ConflictException(HTTPException):
    def __init__(self, detail: str = "Conflit"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class UnprocessableContent(HTTPException):
    def __init__(self, detail: str = "Conflit"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=detail
        )


__all__ = [
    "NotFoundException",
    "BadRequestException",
    "UnauthorizedException",
    "ConflictException",
    "UnprocessableContent",
    "ForbiddenException",
]

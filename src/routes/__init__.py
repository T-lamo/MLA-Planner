#

from fastapi import APIRouter

from core.auth.auth_route import router as auth_router

router = APIRouter()
router.include_router(auth_router)
__all__ = ["router"]

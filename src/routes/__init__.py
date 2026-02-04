#

from fastapi import APIRouter

from core.auth.auth_route import router as auth_router

from .organisation_router import router as organisation
from .pays_router import router as pays

router = APIRouter()
router.include_router(auth_router)
router.include_router(organisation)
router.include_router(pays)

__all__ = ["router"]

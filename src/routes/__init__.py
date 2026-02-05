#

from fastapi import APIRouter

from core.auth.auth_route import router as auth_router

from .campus_router import router as campus
from .membre_router import router as member
from .ministere_router import router as ministre
from .organisation_router import router as organisation
from .pays_router import router as pays

router = APIRouter()
router.include_router(auth_router)
router.include_router(organisation)
router.include_router(pays)
router.include_router(campus)
router.include_router(ministre)
router.include_router(member)


__all__ = ["router"]

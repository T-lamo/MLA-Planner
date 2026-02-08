#

from fastapi import APIRouter

from core.auth.auth_route import router as auth_router

from .campus_router import router as campus
from .chantre_router import router as chantre
from .choriste_router import router as choriste
from .membre_router import router as member
from .ministere_router import router as ministre
from .musicien_router import router as musicien
from .organisation_router import router as organisation
from .pays_router import router as pays
from .pole_router import router as pole

router = APIRouter()
router.include_router(auth_router)
router.include_router(organisation)
router.include_router(pays)
router.include_router(campus)
router.include_router(ministre)
router.include_router(member)
router.include_router(pole)
router.include_router(chantre)
router.include_router(choriste)
router.include_router(musicien)


__all__ = ["router"]

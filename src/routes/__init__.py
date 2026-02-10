#

from fastapi import APIRouter

from core.auth.auth_route import router as auth_router

from .campus_router import router as campus
from .categorie_role_router import router as category_role
from .membre_role_router import router as membre_role
from .membre_router import router as member
from .ministere_router import router as ministre
from .organisation_router import router as organisation
from .pays_router import router as pays
from .pole_router import router as pole
from .role_competence_router import router as role_competence

router = APIRouter()
router.include_router(auth_router)
router.include_router(organisation)
router.include_router(pays)
router.include_router(campus)
router.include_router(ministre)
router.include_router(member)
router.include_router(pole)
router.include_router(category_role)
router.include_router(role_competence)
router.include_router(
    membre_role
)  # Nouveau routeur pour les affectations membres-rôles

__all__ = ["router"]

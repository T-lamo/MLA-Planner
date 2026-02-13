#

from fastapi import APIRouter

from core.auth.auth_route import router as auth_router

from .activite_router import router as activite  # Doit être après planning pour les FK
from .affectation_router import (
    router as affectation,  # Doit être après planning pour les FK
)
from .campus_router import router as campus
from .categorie_role_router import router as category_role
from .equipe_router import router as equipe
from .indisponibilite_router import router as indisponibilite
from .membre_role_router import router as membre_role
from .membre_router import router as member
from .ministere_router import router as ministre
from .organisation_router import router as organisation
from .pays_router import router as pays
from .planning_router import router as planning  # Doit être après slot pour les FK
from .pole_router import router as pole
from .role_competence_router import router as role_competence
from .slot_router import router as slot  # Doit être après membre_role pour les FK

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
router.include_router(membre_role)
router.include_router(indisponibilite)
router.include_router(equipe)  # Doit être après membre et ministre pour les FK
router.include_router(slot)  # Doit être après membre_role pour les FK
router.include_router(planning)  # Doit être après slot pour les FK
router.include_router(affectation)  # Doit être après planning pour les FK
router.include_router(activite)  # Doit être après planning pour les FK

__all__ = ["router"]

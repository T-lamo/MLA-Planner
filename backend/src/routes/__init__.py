#

from fastapi import APIRouter

from core.auth.auth_route import router as auth_router
from notification.notification_router import router as notification

from .activite_router import router as activite  # Doit être après planning pour les FK
from .affectation_router import me_router as affectation_me  # Routes /me — avant /{id}
from .affectation_router import (
    router as affectation,  # Doit être après planning pour les FK
)
from .campus_config_router import router as campus_config
from .campus_router import router as campus
from .categorie_role_router import router as category_role
from .chant_router import router as chant
from .equipe_router import router as equipe
from .indisponibilite_router import router as indisponibilite
from .membre_role_router import router as membre_role
from .membre_router import router as member
from .ministere_router import router as ministre
from .organisation_router import router as organisation
from .pays_router import router as pays
from .planning_router import router as planning  # Doit être après slot pour les FK
from .planning_template_router import router as planning_template
from .pole_router import router as pole
from .profil_router import router as profile
from .role_competence_router import router as role_competence
from .role_router import router as role
from .slot_router import router as slot  # Doit être après membre_role pour les FK
from .team_router import router as team

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
router.include_router(role)
router.include_router(membre_role)
router.include_router(indisponibilite)
router.include_router(equipe)  # Doit être après membre et ministre pour les FK
router.include_router(slot)  # Doit être après membre_role pour les FK
router.include_router(planning)  # Doit être après slot pour les FK
router.include_router(planning_template)
router.include_router(affectation_me)  # Routes /me — avant /{id} pour éviter le conflit
router.include_router(affectation)  # Doit être après planning pour les FK
router.include_router(activite)  # Doit être après planning pour les FK
router.include_router(profile)
router.include_router(team)
router.include_router(notification)
router.include_router(campus_config)  # Campus Configuration (Super Admin)
router.include_router(chant)  # Songbook

__all__ = ["router"]

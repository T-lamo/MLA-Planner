from datetime import datetime
from typing import List, Optional

from fastapi import Depends, status
from sqlmodel import Session

from conf.db.database import Database
from core.auth.auth_dependencies import RoleChecker
from models import MembreCreate, MembreRead, MembreUpdate, UtilisateurRead
from models.membre_role_model import MembreRoleCreate, MembreRoleRead
from models.schema_db_model import Membre
from routes.dependance import get_current_membre
from routes.deps import STANDARD_ADMIN_ONLY_DEPS
from services.membre_service import MembreService

from .base_route_factory import CRUDRouterFactory

admin_only = Depends(RoleChecker(["ADMIN"]))

factory = CRUDRouterFactory(
    service_class=MembreService,
    create_schema=MembreCreate,
    read_schema=MembreRead,
    update_schema=MembreUpdate,
    path="/membres",
    tag="Membres",
    dependencies=STANDARD_ADMIN_ONLY_DEPS,
)

router = factory.router


@router.patch("/utilisateurs/{user_id}/link-membre", response_model=UtilisateurRead)
def link_membre(
    user_id: str, membre_id: str, db: Session = Depends(Database.get_session)
):
    return MembreService(db).link_utilisateur(user_id, membre_id)


# --- ROUTES DÉDIÉES AUX RÔLES (SUB-RESOURCES) ---


@router.get(
    "/{id_membre}/roles",
    response_model=List[MembreRoleRead],
    dependencies=STANDARD_ADMIN_ONLY_DEPS.get("read", []),
)
def get_membre_roles(
    id_membre: str, service: MembreService = Depends(factory.get_service)
):
    """Liste les compétences d'un membre avec chargement optimisé via le repository."""
    return service.get_roles_by_membre(id_membre)


@router.post(
    "/{id_membre}/roles",
    response_model=MembreRoleRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=STANDARD_ADMIN_ONLY_DEPS.get("create", []),
)
def assign_role_to_membre(
    id_membre: str,
    data: MembreRoleCreate,
    service: MembreService = Depends(factory.get_service),
):
    """Affecte une nouvelle compétence à un membre."""
    return service.add_role_to_membre(id_membre, data)


@router.delete(
    "/{id_membre}/roles/{role_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=STANDARD_ADMIN_ONLY_DEPS.get("delete", []),
)
def remove_membre_role(
    id_membre: str,
    role_code: str,
    service: MembreService = Depends(factory.get_service),
):
    """Retire une compétence à un membre (Hard Delete sur la table de liaison)."""
    service.remove_role_from_membre(id_membre, role_code)


@router.get("/me/agenda")
def read_my_personal_agenda(
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    # On injecte directement le Membre au lieu de l'Utilisateur
    current_membre: Membre = Depends(get_current_membre),
    service: MembreService = Depends(factory.get_service),
):
    # On passe directement l'ID du membre au service
    return service.get_personal_agenda(
        membre_id=current_membre.id, from_date=from_date, to_date=to_date
    )

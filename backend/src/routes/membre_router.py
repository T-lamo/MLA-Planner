from datetime import datetime
from typing import List, Optional

from fastapi import Depends, status
from sqlmodel import Session, select

from conf.db.database import Database
from core.auth.auth_dependencies import get_current_active_user
from models import MembreCreate, MembreRead, MembreUpdate, Utilisateur, UtilisateurRead

# MembreSimple et MembreSimpleWithRoles définis dans membre_model (hors __init__)
from models.membre_model import MembreSimpleWithRoles
from models.membre_role_model import MembreRoleCreate, MembreRoleRead
from models.schema_db_model import Membre, MembreRole, Ministere
from routes.dependance import get_current_membre
from routes.deps import STANDARD_ADMIN_ONLY_DEPS
from services.membre_service import MembreService

from .base_route_factory import CRUDRouterFactory

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


@router.get(
    "/by-ministere/{ministere_id}",
    response_model=List[MembreSimpleWithRoles],
    summary="Membres d'un ministère",
    description="Retourne tous les membres actifs liés à un ministère donné.",
)
def list_membres_by_ministere(
    ministere_id: str,
    db: Session = Depends(Database.get_db_for_route),
    _: Utilisateur = Depends(get_current_active_user),
) -> List[MembreSimpleWithRoles]:
    """Liste les membres actifs d'un ministère avec leurs role_codes."""

    ministere = db.exec(select(Ministere).where(Ministere.id == ministere_id)).first()
    if not ministere:
        return []
    membres_actifs = [m for m in ministere.membres if m.actif]
    result: List[MembreSimpleWithRoles] = []
    for m in membres_actifs:
        roles_stmt = select(MembreRole).where(MembreRole.membre_id == m.id)
        roles_assoc = list(db.exec(roles_stmt).all())
        result.append(
            MembreSimpleWithRoles(
                id=m.id,
                nom=m.nom,
                prenom=m.prenom,
                email=m.email,
                telephone=m.telephone,
                actif=m.actif,
                campus_principal_id=m.campus_principal_id,
                date_inscription=m.date_inscription,
                roles=[r.role_code for r in roles_assoc],
            )
        )
    return result


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

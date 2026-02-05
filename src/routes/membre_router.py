from fastapi import Depends
from sqlmodel import Session

from conf.db.database import Database
from core.auth.auth_dependencies import RoleChecker
from models import MembreCreate, MembreRead, MembreUpdate, UtilisateurRead
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

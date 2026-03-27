from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from conf.db.database import Database
from core.auth.auth_dependencies import get_current_active_user
from models import Utilisateur
from models.role_model import RoleRead
from models.schema_db_model import Role

router = APIRouter(prefix="/roles", tags=["Roles"])


def get_db(db: Session = Depends(Database.get_session)) -> Session:
    return db


@router.get(
    "/",
    response_model=List[RoleRead],
    summary="Lister les rôles assignables (hors Super Admin)",
)
def list_roles(
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(get_current_active_user),
) -> List[RoleRead]:
    """
    Retourne tous les rôles disponibles à l'exception du rôle SUPER_ADMIN.
    Requiert une authentification.
    """
    stmt = select(Role).where(Role.libelle != "Super Admin")
    roles = db.exec(stmt).all()
    return [RoleRead(id=r.id, libelle=r.libelle) for r in roles]

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from conf.db.database import Database
from core.auth.auth_dependencies import get_current_active_user
from models import Utilisateur
from models.team_model import CampusTeamRead
from services.team_service import TeamService

router = APIRouter(prefix="/campus", tags=["Team"])


def _get_service(
    db: Session = Depends(Database.get_db_for_route),
) -> TeamService:
    return TeamService(db)


@router.get(
    "/{campus_id}/team",
    response_model=CampusTeamRead,
    summary="Équipe du campus accessible à l'utilisateur connecté",
)
def get_campus_team(
    campus_id: str,
    current_user: Utilisateur = Depends(get_current_active_user),
    service: TeamService = Depends(_get_service),
) -> CampusTeamRead:
    """Retourne les ministères du campus (intersection avec ceux de l'user),
    chacun avec ses membres actifs et leurs rôles compétences."""
    if not current_user.membre_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun profil membre associé à cet utilisateur.",
        )
    return service.get_campus_team(current_user.membre_id, campus_id)

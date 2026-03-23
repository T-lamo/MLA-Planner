# src/routes/indisponibilite_router.py
from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from conf.db.database import Database
from core.auth.auth_dependencies import RoleChecker, get_current_active_user
from models import Utilisateur
from models.indisponibilite_model import (
    IndisponibiliteCreate,
    IndisponibiliteRead,
    IndisponibiliteReadFull,
)
from models.schema_db_model import Indisponibilite
from routes.dependance import get_current_membre
from services.indisponibilite_service import IndisponibiliteService

router = APIRouter(prefix="/indisponibilites", tags=["Indisponibilités"])

admin_or_resp = Depends(RoleChecker(["ADMIN", "RESPONSABLE_MLA"]))


# ------------------------------------------------------------------
# Routes MEMBRE (utilisateur connecté avec un profil membre)
# ------------------------------------------------------------------


@router.post(
    "/",
    response_model=IndisponibiliteRead,
    status_code=status.HTTP_201_CREATED,
)
def declare_indisponibilite(
    payload: IndisponibiliteCreate,
    db: Session = Depends(Database.get_db_for_route),
    current_user: Utilisateur = Depends(get_current_active_user),
) -> Indisponibilite:
    """Membre déclare sa propre indisponibilité."""
    membre = get_current_membre(current_user)
    svc = IndisponibiliteService(db)
    return svc.create_by_membre(payload, membre.id)


@router.get("/me", response_model=List[IndisponibiliteReadFull])
def get_my_indisponibilites(
    db: Session = Depends(Database.get_session),
    current_user: Utilisateur = Depends(get_current_active_user),
) -> List[IndisponibiliteReadFull]:
    """Membre consulte ses propres indisponibilités."""
    membre = get_current_membre(current_user)
    return IndisponibiliteService(db).get_for_membre(membre.id)


@router.delete("/{indisp_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_indisponibilite(
    indisp_id: str,
    db: Session = Depends(Database.get_db_for_route),
    current_user: Utilisateur = Depends(get_current_active_user),
) -> None:
    """Membre supprime sa propre indisponibilité (si non validée)."""
    membre = get_current_membre(current_user)
    IndisponibiliteService(db).delete_by_membre(indisp_id, membre.id)


# ------------------------------------------------------------------
# Routes ADMIN / RESPONSABLE
# ------------------------------------------------------------------


@router.get(
    "/campus/{campus_id}",
    response_model=List[IndisponibiliteReadFull],
    dependencies=[admin_or_resp],
)
def list_by_campus(
    campus_id: str,
    ministere_id: Optional[str] = None,
    date_debut: Optional[str] = None,
    date_fin: Optional[str] = None,
    validee_only: bool = False,
    *,
    db: Session = Depends(Database.get_session),
) -> List[IndisponibiliteReadFull]:
    """Admin/Responsable liste les indisponibilités d'un campus."""
    return IndisponibiliteService(db).get_for_campus(
        campus_id,
        validee_only=validee_only,
        ministere_id=ministere_id,
        date_debut=date_debut,
        date_fin=date_fin,
    )


@router.patch(
    "/{indisp_id}/valider",
    response_model=IndisponibiliteReadFull,
    dependencies=[admin_or_resp],
)
def valider_indisponibilite(
    indisp_id: str,
    db: Session = Depends(Database.get_db_for_route),
) -> IndisponibiliteReadFull:
    """Admin/Responsable valide une indisponibilité."""
    return IndisponibiliteService(db).valider(indisp_id)


@router.delete(
    "/{indisp_id}/admin",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[admin_or_resp],
)
def admin_delete_indisponibilite(
    indisp_id: str,
    db: Session = Depends(Database.get_db_for_route),
) -> None:
    """Admin supprime n'importe quelle indisponibilité."""
    IndisponibiliteService(db).admin_delete(indisp_id)


@router.get(
    "/campus/{campus_id}/period",
    response_model=List[IndisponibiliteReadFull],
    dependencies=[admin_or_resp],
)
def get_validated_for_period(
    campus_id: str,
    date_debut: str,
    date_fin: str,
    db: Session = Depends(Database.get_session),
) -> List[IndisponibiliteReadFull]:
    """Indisponibilités validées chevauchant une période (pour le planning)."""
    return IndisponibiliteService(db).get_validated_for_campus_period(
        campus_id, date_debut, date_fin
    )

# src/services/indisponibilite_service.py
from typing import Optional

from sqlmodel import Session

from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
from models import Membre
from models.indisponibilite_model import (
    IndisponibiliteCreate,
    IndisponibiliteReadFull,
)
from models.schema_db_model import Indisponibilite
from repositories.indisponibilite_repository import IndisponibiliteRepository


class IndisponibiliteService:
    """Service métier pour les indisponibilités."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = IndisponibiliteRepository(db)

    # ------------------------------------------------------------------
    # Helpers privés (SRP)
    # ------------------------------------------------------------------

    def _get_or_404(self, indisp_id: str) -> Indisponibilite:
        obj = self.db.get(Indisponibilite, indisp_id)
        if not obj:
            raise AppException(ErrorRegistry.INDISP_NOT_FOUND)
        return obj

    def _check_owner(self, indisp: Indisponibilite, membre_id: str) -> None:
        if indisp.membre_id != membre_id:
            raise AppException(ErrorRegistry.INDISP_NOT_OWNER)

    def _check_not_validated(self, indisp: Indisponibilite) -> None:
        if indisp.validee:
            raise AppException(ErrorRegistry.INDISP_ALREADY_VALIDATED)

    def _check_no_overlap(
        self,
        membre_id: str,
        date_debut: str,
        date_fin: str,
        ministere_id: Optional[str],
        *,
        exclude_id: Optional[str] = None,
    ) -> None:
        hits = self.repo.get_overlapping(
            membre_id,
            date_debut,
            date_fin,
            ministere_id,
            exclude_id=exclude_id,
        )
        if hits:
            raise AppException(ErrorRegistry.INDISP_OVERLAP)

    def _build_full(self, indisp: Indisponibilite) -> IndisponibiliteReadFull:
        membre = indisp.membre
        ministere = indisp.ministere
        return IndisponibiliteReadFull(
            id=indisp.id,
            membre_id=indisp.membre_id,
            ministere_id=indisp.ministere_id,
            date_debut=indisp.date_debut,
            date_fin=indisp.date_fin,
            motif=indisp.motif,
            validee=indisp.validee,
            membre_nom=membre.nom if membre else "",
            membre_prenom=membre.prenom if membre else "",
            ministere_libelle=(ministere.nom if ministere else None),
        )

    # ------------------------------------------------------------------
    # Actions membre
    # ------------------------------------------------------------------

    def create_by_membre(
        self,
        payload: IndisponibiliteCreate,
        current_membre_id: str,
    ) -> Indisponibilite:
        """Déclaration par le membre lui-même."""
        if payload.membre_id != current_membre_id:
            raise AppException(ErrorRegistry.INDISP_NOT_OWNER)
        membre = self.db.get(Membre, current_membre_id)
        if not membre:
            raise AppException(ErrorRegistry.MEMBRE_NOT_FOUND)
        if payload.date_debut and payload.date_fin:
            self._check_no_overlap(
                current_membre_id,
                payload.date_debut,
                payload.date_fin,
                payload.ministere_id,
            )
        obj = Indisponibilite(**payload.model_dump())
        self.db.add(obj)
        self.db.flush()
        self.db.refresh(obj)
        return obj

    def get_for_membre(self, membre_id: str) -> list[IndisponibiliteReadFull]:
        """Vue membre : toutes ses indisponibilités."""
        rows = self.repo.get_by_membre(membre_id)
        return [self._build_full(r) for r in rows]

    def delete_by_membre(self, indisp_id: str, membre_id: str) -> None:
        """Suppression par le membre (seulement si non validée)."""
        indisp = self._get_or_404(indisp_id)
        self._check_owner(indisp, membre_id)
        self._check_not_validated(indisp)
        self.db.delete(indisp)
        self.db.flush()

    # ------------------------------------------------------------------
    # Actions admin / responsable
    # ------------------------------------------------------------------

    def valider(self, indisp_id: str) -> IndisponibiliteReadFull:
        """Admin/Responsable valide une indisponibilité."""
        indisp = self._get_or_404(indisp_id)
        self._check_not_validated(indisp)
        indisp.validee = True
        self.db.add(indisp)
        self.db.flush()
        self.db.refresh(indisp)
        return self._build_full(indisp)

    def get_for_campus(
        self,
        campus_id: str,
        *,
        validee_only: bool = False,
        ministere_id: Optional[str] = None,
        date_debut: Optional[str] = None,
        date_fin: Optional[str] = None,
    ) -> list[IndisponibiliteReadFull]:
        """Vue admin : indisponibilités filtrées d'un campus."""
        rows = self.repo.get_by_campus(campus_id)
        rows = self._apply_filters(
            rows,
            validee_only=validee_only,
            ministere_id=ministere_id,
            date_debut=date_debut,
            date_fin=date_fin,
        )
        return [self._build_full(r) for r in rows]

    def _apply_filters(
        self,
        rows: list[Indisponibilite],
        *,
        validee_only: bool,
        ministere_id: Optional[str],
        date_debut: Optional[str],
        date_fin: Optional[str],
    ) -> list[Indisponibilite]:
        """Filtre en mémoire après la requête principale."""
        if validee_only:
            rows = [r for r in rows if r.validee]
        if ministere_id:
            rows = [r for r in rows if r.ministere_id == ministere_id]
        if date_debut:
            rows = [
                r for r in rows if r.date_fin is not None and r.date_fin >= date_debut
            ]
        if date_fin:
            rows = [
                r for r in rows if r.date_debut is not None and r.date_debut <= date_fin
            ]
        return rows

    def admin_delete(self, indisp_id: str) -> None:
        """Suppression admin (sans restriction de statut)."""
        indisp = self._get_or_404(indisp_id)
        self.db.delete(indisp)
        self.db.flush()

    def get_validated_for_campus_period(
        self,
        campus_id: str,
        date_debut: str,
        date_fin: str,
    ) -> list[IndisponibiliteReadFull]:
        """Indisponibilités validées qui chevauchent une période."""
        rows = self.repo.get_by_campus(campus_id)
        active = [
            r
            for r in rows
            if r.validee
            and r.date_debut is not None
            and r.date_fin is not None
            and r.date_debut <= date_fin
            and r.date_fin >= date_debut
        ]
        return [self._build_full(r) for r in active]

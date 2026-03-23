import logging
from typing import Any, List, cast

from sqlalchemy import or_
from sqlalchemy.orm import selectinload
from sqlmodel import Session, col, select

from models.schema_db_model import (
    CampusMinistereLink,
    Membre,
    Ministere,
)
from models.team_model import CampusTeamRead, TeamMemberRead, TeamMinistereRead
from services.profile_service import ProfileService

logger = logging.getLogger(__name__)


class TeamService:
    def __init__(self, db: Session):
        self.db = db
        self._profile_svc = ProfileService(db)

    def get_campus_team(self, membre_id: str, campus_id: str) -> CampusTeamRead:
        """Retourne les ministères accessibles (intersection user ∩ campus),
        chacun avec ses membres actifs et leurs rôles compétences."""
        target_ids = self._resolve_target_ministere_ids(membre_id, campus_id)
        if not target_ids:
            return CampusTeamRead(ministeres=[])

        ministeres = self._load_ministeres_with_membres(target_ids)
        return CampusTeamRead(ministeres=[self._build_ministere(m) for m in ministeres])

    # ------------------------------------------------------------------
    # Helpers privés
    # ------------------------------------------------------------------

    def _resolve_target_ministere_ids(
        self, membre_id: str, campus_id: str
    ) -> List[str]:
        """Intersection : ministères du campus ∩ ministères de l'utilisateur."""
        links = self.db.exec(
            select(CampusMinistereLink).where(
                CampusMinistereLink.campus_id == campus_id
            )
        ).all()
        campus_ids = {lnk.ministere_id for lnk in links}

        user_ministeres = self._profile_svc.get_my_ministeres_by_campus(
            membre_id, campus_id
        )
        user_ids = {m.id for m in user_ministeres}

        return list(campus_ids & user_ids)

    def _load_ministeres_with_membres(self, target_ids: List[str]) -> List[Ministere]:
        """Charge les ministères avec eager-loading membres + roles_assoc."""
        conditions = [col(cast(Any, Ministere.id)) == mid for mid in target_ids]
        return list(
            self.db.exec(
                select(Ministere)
                .where(or_(*conditions))
                .options(
                    selectinload(cast(Any, Ministere.membres)).selectinload(
                        cast(Any, Membre.roles_assoc)
                    )
                )
            ).all()
        )

    def _build_ministere(self, ministere: Ministere) -> TeamMinistereRead:
        membres = [
            self._build_member(m)
            for m in ministere.membres
            if m.deleted_at is None and m.actif
        ]
        return TeamMinistereRead(
            id=ministere.id,
            nom=ministere.nom,
            membres=membres,
        )

    def _build_member(self, membre: Membre) -> TeamMemberRead:
        roles = [assoc.role_code for assoc in membre.roles_assoc]
        return TeamMemberRead(
            id=membre.id,
            nom=membre.nom,
            prenom=membre.prenom,
            roles=roles,
        )

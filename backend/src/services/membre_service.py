from datetime import datetime, timedelta
from typing import Any, List, Optional, cast

from sqlmodel import Session, select

from core.exceptions import BadRequestException, NotFoundException
from core.exceptions.app_exception import AppException
from core.exceptions.exceptions import ConflictException
from core.message import ErrorRegistry
from models import Membre, MembreCreate, MembreRead, MembreUpdate, Utilisateur
from models.membre_role_model import MembreRoleCreate
from models.schema_db_model import Campus, MembreRole, Ministere, Pole, RoleCompetence
from repositories.campus_repository import CampusRepository
from repositories.membre_repository import MembreRepository
from repositories.ministere_repository import MinistereRepository
from repositories.pole_repository import PoleRepository
from services.base_service import BaseService
from services.planing_service import PlanningServiceSvc


class MembreService(BaseService[MembreCreate, MembreRead, MembreUpdate, Membre]):
    def __init__(self, db: Session):
        super().__init__(repo=MembreRepository(db), resource_name="Membre")
        self.db = db
        self.campus_repo = CampusRepository(db)
        self.min_repo = MinistereRepository(db)
        self.pole_repo = PoleRepository(db)
        self.planning_svc = PlanningServiceSvc(db)

    def create(self, data: MembreCreate) -> Membre:
        """Crée un membre avec ses multiples rattachés (N:N)."""

        membre_data = data.model_dump(
            exclude={"campus_ids", "ministere_ids", "pole_ids"}
        )
        db_membre = Membre(**membre_data)

        if data.campus_ids:
            for c_id in data.campus_ids:
                campus = self.campus_repo.get_by_id(c_id)
                if not campus:
                    raise NotFoundException(f"Campus {c_id} introuvable.")
                # pylint: disable=no-member
                cast(List[Any], db_membre.campuses).append(campus)

        if data.ministere_ids:
            for m_id in data.ministere_ids:
                minis = self.min_repo.get_by_id(m_id)
                if not minis:
                    raise NotFoundException(f"Ministère {m_id} introuvable.")
                # pylint: disable=no-member
                cast(List[Any], db_membre.ministeres).append(minis)

        if data.pole_ids:
            for p_id in data.pole_ids:
                pole = self.pole_repo.get_by_id(p_id)
                if not pole:
                    raise NotFoundException(f"Pôle {p_id} introuvable.")
                # pylint: disable=no-member
                cast(List[Any], db_membre.poles).append(pole)

        return self.repo.create(db_membre)

    # Correction W0237 (signature matching) et W0622 (builtin override)
    def update(self, identifiant: str, data: MembreUpdate) -> Membre:
        """Mise à jour incluant la synchronisation des listes N:N."""
        db_membre = self.get_one(identifiant)

        # Mise à jour des champs simples
        update_data = data.model_dump(
            exclude_unset=True, exclude={"campus_ids", "ministere_ids", "pole_ids"}
        )
        for key, value in update_data.items():
            setattr(db_membre, key, value)

        # Synchronisation
        if data.campus_ids is not None:
            campuses = [self.db.get(Campus, cid) for cid in data.campus_ids]
            db_membre.campuses = [c for c in campuses if c is not None]

        if data.ministere_ids is not None:
            ministeres = [self.db.get(Ministere, mid) for mid in data.ministere_ids]
            db_membre.ministeres = [m for m in ministeres if m is not None]

        if data.pole_ids is not None:
            poles = [self.db.get(Pole, pid) for pid in data.pole_ids]
            db_membre.poles = [p for p in poles if p is not None]

        self.db.add(db_membre)
        self.db.flush()
        self.db.refresh(db_membre)
        return db_membre

    def link_utilisateur(self, user_id: str, membre_id: str) -> Utilisateur:
        membre = self.get_one(membre_id)
        user = self.db.get(Utilisateur, user_id)

        if not user:
            raise NotFoundException("Utilisateur introuvable.")

        # 1. Vérifier si ce membre a déjà un compte
        if self.db.exec(
            select(Utilisateur).where(Utilisateur.membre_id == membre_id)
        ).first():
            raise BadRequestException("Ce membre est déjà lié à un compte utilisateur.")

        # 2. Vérifier si cet utilisateur est déjà lié à un autre membre
        if user.membre_id:
            raise BadRequestException("Cet utilisateur est déjà lié à un membre.")

        user.membre_id = membre.id
        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)
        return user

    def _after_delete_hook(self, obj: Membre) -> None:
        # On casse le lien avec l'utilisateur (SET NULL)
        if obj.utilisateur:
            obj.utilisateur.membre_id = None
            self.db.add(obj.utilisateur)

        self.db.flush()

    def get_roles_by_membre(self, membre_id: str) -> List[MembreRole]:
        """
        Récupère tous les rôles d'un membre en utilisant
        le chargement optimisé du repository.
        """
        # Appel à la nouvelle méthode du repository
        membre = self.repo.get_membre_with_roles(membre_id)  # type: ignore

        if not membre:
            raise NotFoundException(f"Membre {membre_id} introuvable.")

        # On retourne directement la liste chargée par SQLAlchemy
        return membre.roles_assoc

    def add_role_to_membre(self, membre_id: str, data: MembreRoleCreate) -> MembreRole:
        """Assigne un rôle avec validation d'intégrité."""
        self.get_one(membre_id)

        # Vérifier l'existence du rôle technique
        role = self.db.get(RoleCompetence, data.role_code.upper())
        if not role:
            raise NotFoundException(f"Le rôle {data.role_code} n'existe pas.")

        # Vérifier si l'association existe déjà (PK composite)
        existing = self.db.get(MembreRole, (membre_id, data.role_code.upper()))
        if existing:
            raise ConflictException("Ce membre possède déjà ce rôle.")

        db_obj = MembreRole.model_validate(data)
        db_obj.membre_id = membre_id  # Sécurité : force l'ID du membre de l'URL

        self.db.add(db_obj)
        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj

    def remove_role_from_membre(self, membre_id: str, role_code: str) -> None:
        """Supprime une affectation spécifique."""
        aff = self.db.get(MembreRole, (membre_id, role_code.upper()))
        if not aff:
            raise NotFoundException("Affectation membre/rôle introuvable.")

        self.db.delete(aff)
        self.db.flush()

    def get_personal_agenda(
        self,
        membre_id: str,
        campus_id: Optional[str] = None,
        from_date=None,
        to_date=None,
    ):
        """Récupère l'agenda pour un membre dans un campus spécifique."""
        membre = self.repo.get_by_id(membre_id)
        if not membre:
            raise AppException(ErrorRegistry.MEMBRE_NOT_FOUND)

        # NOUVELLE LOGIQUE : Si aucun campus_id fourni, on prend le premier rattaché
        target_campus_id = campus_id
        if not target_campus_id:
            if not membre.campuses:
                raise AppException(ErrorRegistry.MEMBRE_CAMPUS_MISSING)
            target_campus_id = membre.campuses[0].id

        start = from_date or datetime.now()
        end = to_date or (start + timedelta(days=90))

        return self.planning_svc.get_member_agenda_full(
            membre_id=membre_id, campus_id=target_campus_id, start=start, end=end
        )

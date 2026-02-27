from datetime import datetime, timedelta
from typing import List, Optional

from sqlmodel import Session, select

from core.exceptions import BadRequestException, NotFoundException
from core.exceptions.app_exception import AppException
from core.exceptions.exceptions import ConflictException
from core.message import ErrorRegistry
from models import Membre, MembreCreate, MembreRead, MembreUpdate, Utilisateur
from models.membre_role_model import MembreRoleCreate
from models.schema_db_model import MembreRole, RoleCompetence
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
        if not data.campus_ids:
            raise BadRequestException(
                "Un membre doit être rattaché à au moins un campus."
            )

        # Préparation de l'objet sans les relations N:N
        membre_data = data.model_dump(
            exclude={"campus_ids", "ministere_ids", "pole_ids"}
        )
        db_membre = Membre(**membre_data)

        # Synchronisation
        self._sync_relations(
            db_membre,
            campus_ids=data.campus_ids,
            min_ids=data.ministere_ids,
            pole_ids=data.pole_ids,
        )

        self.db.add(db_membre)
        self.db.flush()  # Prépare l'insertion sans fermer la transaction
        return db_membre

    def update(self, identifiant: str, data: MembreUpdate) -> Membre:
        db_membre = self.get_one(identifiant)
        if hasattr(db_membre, "deleted_at") and db_membre.deleted_at:
            raise BadRequestException("Impossible de modifier un membre supprimé.")

        update_data = data.model_dump(
            exclude_unset=True, exclude={"campus_ids", "ministere_ids", "pole_ids"}
        )
        for key, value in update_data.items():
            setattr(db_membre, key, value)

        self._sync_relations(
            db_membre,
            campus_ids=data.campus_ids,
            min_ids=data.ministere_ids,
            pole_ids=data.pole_ids,
            is_update=True,
        )

        self.db.add(db_membre)
        self.db.flush()
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

    def delete(self, identifiant: str) -> None:
        """
        Implémentation du Soft Delete.
        Met à jour 'deleted_at' au lieu de supprimer l'enregistrement.
        """
        db_membre = self.get_one(identifiant)

        if db_membre.deleted_at:
            return  # Déjà supprimé, idempotent

        db_membre.deleted_at = datetime.now()

        # Exécution du hook pour nettoyer les dépendances (ex: lien utilisateur)
        self._after_delete_hook(db_membre)

        self.db.add(db_membre)
        self.db.flush()

    def _sync_relations(
        self,
        membre: Membre,
        *,
        campus_ids: Optional[List[str]] = None,
        min_ids: Optional[List[str]] = None,
        pole_ids: Optional[List[str]] = None,
        is_update: bool = False,
    ) -> None:
        """
        Logique interne de synchronisation des collections SQLModel.
        En mode update, remplace proprement les collections.
        """
        if campus_ids is not None:
            # Validation métier même en update
            if is_update and len(campus_ids) == 0:
                raise BadRequestException(
                    "Un membre doit conserver au moins un campus."
                )

            campuses = []
            for c_id in campus_ids:
                c = self.campus_repo.get_by_id(c_id)
                if not c:
                    raise NotFoundException(f"Campus {c_id} introuvable.")
                campuses.append(c)
            membre.campuses = campuses

        if min_ids is not None:
            ministeres = []
            for m_id in min_ids:
                m = self.min_repo.get_by_id(m_id)
                if not m:
                    raise NotFoundException(f"Ministère {m_id} introuvable.")
                ministeres.append(m)
            membre.ministeres = ministeres

        if pole_ids is not None:
            poles = []
            for p_id in pole_ids:
                p = self.pole_repo.get_by_id(p_id)
                if not p:
                    raise NotFoundException(f"Pôle {p_id} introuvable.")
                poles.append(p)
            membre.poles = poles

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

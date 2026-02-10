from typing import List

from sqlmodel import Session, select

from core.exceptions import BadRequestException, NotFoundException
from core.exceptions.exceptions import ConflictException
from models import Membre, MembreCreate, MembreRead, MembreUpdate, Utilisateur
from models.membre_role_model import MembreRoleCreate
from models.schema_db_model import MembreRole, RoleCompetence
from repositories.membre_repository import MembreRepository
from repositories.ministere_repository import MinistereRepository
from repositories.pole_repository import PoleRepository
from services.base_service import BaseService


class MembreService(BaseService[MembreCreate, MembreRead, MembreUpdate, Membre]):
    def __init__(self, db: Session):
        super().__init__(repo=MembreRepository(db), resource_name="Membre")
        self.db = db
        self.min_repo = MinistereRepository(db)
        self.pole_repo = PoleRepository(db)

    def create(self, data: MembreCreate) -> Membre:
        # Validation UUID existence
        if data.ministere_id and not self.min_repo.get_by_id(data.ministere_id):
            raise NotFoundException(f"Ministère {data.ministere_id} introuvable.")
        if data.pole_id and not self.pole_repo.get_by_id(data.pole_id):
            raise NotFoundException(f"Pôle {data.pole_id} introuvable.")

        return self.repo.create(Membre(**data.model_dump()))

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
        self.db.commit()
        self.db.refresh(user)
        return user

    def _after_delete_hook(self, obj: Membre) -> None:
        # On casse le lien avec l'utilisateur (SET NULL)
        if obj.utilisateur:
            obj.utilisateur.membre_id = None
            self.db.add(obj.utilisateur)

        self.db.commit()

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
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def remove_role_from_membre(self, membre_id: str, role_code: str) -> None:
        """Supprime une affectation spécifique."""
        aff = self.db.get(MembreRole, (membre_id, role_code.upper()))
        if not aff:
            raise NotFoundException("Affectation membre/rôle introuvable.")

        self.db.delete(aff)
        self.db.commit()

from sqlmodel import Session

from core.exceptions import ConflictException, NotFoundException
from models import (
    Membre,
    MembreRole,
    MembreRoleCreate,
    MembreRoleRead,
    MembreRoleUpdate,
    RoleCompetence,
)
from repositories.membre_role_repository import MembreRoleRepository

from .base_service import BaseService


class MembreRoleService(
    BaseService[MembreRoleCreate, MembreRoleRead, MembreRoleUpdate, MembreRole]
):
    def __init__(self, db: Session):
        self.repo = MembreRoleRepository(db)
        super().__init__(self.repo, resource_name="Affectation Membre-Rôle")

    def create(self, data: MembreRoleCreate) -> MembreRole:
        # 1. Vérifier si l'affectation existe déjà
        if self.repo.get_by_id((data.membre_id, data.role_code)):
            raise ConflictException("Ce membre possède déjà ce rôle.")

        # 2. Vérifier l'existence des entités parentes (Sécurité intégrité)
        if not self.repo.db.get(Membre, data.membre_id):
            raise NotFoundException("Membre introuvable.")
        if not self.repo.db.get(RoleCompetence, data.role_code):
            raise NotFoundException("Rôle technique introuvable.")

        db_obj = MembreRole.model_validate(data)
        return self.repo.create(db_obj)

    def update_composite(
        self, membre_id: str, role_code: str, data: MembreRoleUpdate
    ) -> MembreRole:
        obj = self.get_one(f"{membre_id}:{role_code}")
        update_data = data.model_dump(exclude_unset=True)
        return self.repo.update(obj, update_data)

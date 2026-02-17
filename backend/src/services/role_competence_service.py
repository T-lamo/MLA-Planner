from sqlmodel import Session

from core.exceptions import ConflictException, NotFoundException
from models import (
    CategorieRole,
    RoleCompetence,
    RoleCompetenceCreate,
    RoleCompetenceRead,
    RoleCompetenceUpdate,
)
from repositories.role_competence_repository import RoleCompetenceRepository

from .base_service import BaseService


class RoleCompetenceService(
    BaseService[
        RoleCompetenceCreate, RoleCompetenceRead, RoleCompetenceUpdate, RoleCompetence
    ]
):
    def __init__(self, db: Session):
        self.repo = RoleCompetenceRepository(db)
        super().__init__(self.repo, resource_name="Rôle Compétence")

    def create(self, data: RoleCompetenceCreate) -> RoleCompetence:
        # 1. Vérifier si le code existe déjà
        if self.repo.get_by_id(data.code):
            raise ConflictException(f"Le rôle avec le code '{data.code}' existe déjà.")

        # 2. Vérifier si la catégorie parente existe
        cat = self.repo.db.get(CategorieRole, data.categorie_code)
        if not cat:
            raise NotFoundException(f"Catégorie '{data.categorie_code}' introuvable.")

        db_obj = RoleCompetence.model_validate(data)
        return self.repo.create(db_obj)

    def update(self, identifiant: str, data: RoleCompetenceUpdate) -> RoleCompetence:
        obj = self.get_one(identifiant)
        update_data = data.model_dump(exclude_unset=True)

        # Sécurité : Si on change la catégorie, on vérifie son existence
        if "categorie_code" in update_data and update_data["categorie_code"]:
            cat = self.repo.db.get(CategorieRole, update_data["categorie_code"])
            if not cat:
                raise NotFoundException("Nouvelle catégorie introuvable.")

        return self.repo.update(obj, update_data)

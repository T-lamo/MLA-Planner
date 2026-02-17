from core.exceptions import ConflictException
from models import (
    CategorieRole,
    CategorieRoleCreate,
    CategorieRoleRead,
    CategorieRoleUpdate,
)
from repositories.category_role_repository import CategorieRoleRepository
from services.base_service import BaseService
from sqlmodel import Session


class CategorieRoleService(
    BaseService[
        CategorieRoleCreate, CategorieRoleRead, CategorieRoleUpdate, CategorieRole
    ]
):
    def __init__(self, db: Session):
        self.repo = CategorieRoleRepository(db)
        super().__init__(self.repo, resource_name="Catégorie de Rôle")

    def create(self, data: CategorieRoleCreate) -> CategorieRole:
        # Vérification préventive pour la PK naturelle
        if self.repo.get_by_id(data.code):
            raise ConflictException(f"Le code '{data.code}' est déjà utilisé.")

        db_obj = CategorieRole.model_validate(data)
        return self.repo.create(db_obj)

    def update(self, identifiant: str, data: CategorieRoleUpdate) -> CategorieRole:
        db_obj = self.get_one(identifiant)
        update_data = data.model_dump(exclude_unset=True)
        return self.repo.update(db_obj, update_data)

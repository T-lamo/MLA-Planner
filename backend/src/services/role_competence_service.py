from typing import Dict, List, Optional

from sqlmodel import Session

from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
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
            raise AppException(ErrorRegistry.ROLE_COMP_DUPLICATE, code=data.code)

        # 2. Vérifier si la catégorie parente existe
        cat = self.repo.db.get(CategorieRole, data.categorie_code)
        if not cat:
            raise AppException(ErrorRegistry.ROLE_CAT_NOT_FOUND)

        db_obj = RoleCompetence.model_validate(data)
        return self.repo.create(db_obj)

    def update(self, identifiant: str, data: RoleCompetenceUpdate) -> RoleCompetence:
        obj = self.get_one(identifiant)
        update_data = data.model_dump(exclude_unset=True)

        # Sécurité : Si on change la catégorie, on vérifie son existence
        if "categorie_code" in update_data and update_data["categorie_code"]:
            cat = self.repo.db.get(CategorieRole, update_data["categorie_code"])
            if not cat:
                raise AppException(ErrorRegistry.ROLE_CAT_NOT_FOUND)

        return self.repo.update(obj, update_data)

    def list_grouped_by_category(
        self, ministere_id: Optional[str] = None
    ) -> List[Dict]:
        if ministere_id:
            roles = self.repo.get_all_with_categories_for_ministere(ministere_id)
        else:
            roles = self.repo.get_all_with_categories()

        # Groupement manuel pour garder l'ordre du tri SQL
        grouped_dict: Dict[str, Dict] = {}
        for r in roles:
            cat = r.categorie
            if cat.code not in grouped_dict:
                grouped_dict[cat.code] = {
                    "categorie_code": cat.code,
                    "categorie_libelle": cat.libelle,
                    "roles": [],
                }
            grouped_dict[cat.code]["roles"].append(RoleCompetenceRead.model_validate(r))

        return list(grouped_dict.values())

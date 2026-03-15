"""
Schémas Pydantic pour le module Campus Configuration.

Ce module définit les schémas de requête et de réponse utilisés
par les endpoints /config/*.
"""

from typing import Any, Dict, List, Optional

from pydantic import ConfigDict
from sqlmodel import SQLModel

from models.campus_model import CampusRead
from models.categorie_role_model import CategorieRoleRead
from models.ministere_model import MinistereRead
from models.role_competence_model import RoleCompetenceRead
from models.role_model import RoleRead

# -------------------------
# PAYLOADS (entrées)
# -------------------------


class MinistereConfigCreate(SQLModel):
    """Payload pour créer ou réutiliser un ministère dans un campus."""

    nom: str = ""
    description: Optional[str] = None

    model_config = ConfigDict(  # type: ignore[assignment]
        json_schema_extra={"example": {"nom": "Louange", "description": None}}
    )


class CategorieConfigCreate(SQLModel):
    """Payload pour créer ou réutiliser une catégorie dans un ministère."""

    nom: str = ""
    description: Optional[str] = None

    model_config = ConfigDict(  # type: ignore[assignment]
        json_schema_extra={"example": {"nom": "Chant", "description": None}}
    )


class RoleCompetenceConfigCreate(SQLModel):
    """Payload pour créer ou réutiliser un rôle compétence dans une catégorie."""

    code: str = ""
    libelle: str = ""
    description: Optional[str] = None

    model_config = ConfigDict(  # type: ignore[assignment]
        json_schema_extra={
            "example": {
                "code": "SOPRANO",
                "libelle": "Voix Soprano",
                "description": None,
            }
        }
    )


class MinistereConfigUpdate(SQLModel):
    """Payload pour mettre à jour un ministère."""

    nom: Optional[str] = None
    description: Optional[str] = None


class CategorieConfigUpdate(SQLModel):
    """Payload pour mettre à jour une catégorie."""

    nom: Optional[str] = None
    description: Optional[str] = None


class RoleCompetenceConfigUpdate(SQLModel):
    """Payload pour mettre à jour un rôle compétence (code immuable)."""

    libelle: Optional[str] = None
    description: Optional[str] = None


# -------------------------
# RÉPONSES
# -------------------------


class MinistereConfigResponse(SQLModel):
    """Réponse enrichie pour l'ajout d'un ministère à un campus."""

    ministere: MinistereRead
    created: bool  # True si l'entité vient d'être créée
    linked: bool  # True si le lien campus-ministère vient d'être créé

    model_config = ConfigDict(from_attributes=True)  # type: ignore[assignment]


class CategorieConfigResponse(SQLModel):
    """Réponse enrichie pour l'ajout d'une catégorie à un ministère."""

    categorie: CategorieRoleRead
    created: bool

    model_config = ConfigDict(from_attributes=True)  # type: ignore[assignment]


class RoleCompetenceConfigResponse(SQLModel):
    """Réponse enrichie pour l'ajout d'un rôle compétence à une catégorie."""

    role_competence: RoleCompetenceRead
    created: bool

    model_config = ConfigDict(from_attributes=True)  # type: ignore[assignment]


class RbacRolesInitResponse(SQLModel):
    """Réponse pour l'initialisation des rôles RBAC d'un ministère."""

    roles: List[RoleRead]
    created_count: int

    model_config = ConfigDict(from_attributes=True)  # type: ignore[assignment]


class StatutsInitResponse(SQLModel):
    """Réponse pour l'initialisation des statuts planning et affectation."""

    statuts_planning: List[str]
    statuts_affectation: List[str]

    model_config = ConfigDict(from_attributes=True)  # type: ignore[assignment]


# -------------------------
# SETUP CAMPUS (opération complète)
# -------------------------


class RoleSetupItem(SQLModel):
    """Un rôle compétence dans le payload de setup campus."""

    code: str = ""
    libelle: str = ""
    description: Optional[str] = None


class CategorieSetupItem(SQLModel):
    """Une catégorie avec ses rôles dans le payload de setup campus."""

    nom: str = ""
    description: Optional[str] = None
    roles: List[RoleSetupItem] = []


class MinistereSetupItem(SQLModel):
    """Un ministère avec ses catégories dans le payload de setup campus."""

    nom: str = ""
    description: Optional[str] = None
    init_rbac: bool = True
    categories: List[CategorieSetupItem] = []


class CampusSetupPayload(SQLModel):
    """Payload pour la configuration complète d'un campus en une requête."""

    init_statuts: bool = True
    ministeres: List[MinistereSetupItem] = []


class CampusSetupResult(SQLModel):
    """Résultat du setup complet d'un campus."""

    campus_id: str
    ministeres_created: int
    ministeres_linked: int
    categories_created: int
    roles_created: int
    rbac_roles_created: int
    statuts_initialises: bool
    summary: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)  # type: ignore[assignment]


class MinistereWithCategoriesDict(SQLModel):
    """Vue simplifiée d'un ministère avec ses catégories dans le résumé campus."""

    id: str
    nom: str
    categories: List[Dict[str, Any]] = []

    model_config = ConfigDict(from_attributes=True)  # type: ignore[assignment]


class CampusConfigSummary(SQLModel):
    """Résumé complet de la configuration d'un campus."""

    campus_id: str
    campus_nom: str
    ministeres: List[Dict[str, Any]]
    statuts_planning: List[str]
    statuts_affectation: List[str]

    model_config = ConfigDict(from_attributes=True)  # type: ignore[assignment]


# Re-exports pour accès depuis models/
__all__ = [
    "MinistereConfigCreate",
    "CategorieConfigCreate",
    "RoleCompetenceConfigCreate",
    "MinistereConfigUpdate",
    "CategorieConfigUpdate",
    "RoleCompetenceConfigUpdate",
    "MinistereConfigResponse",
    "CategorieConfigResponse",
    "RoleCompetenceConfigResponse",
    "RbacRolesInitResponse",
    "StatutsInitResponse",
    "CampusConfigSummary",
    "RoleSetupItem",
    "CategorieSetupItem",
    "MinistereSetupItem",
    "CampusSetupPayload",
    "CampusSetupResult",
    "CampusRead",
    "MinistereRead",
    "CategorieRoleRead",
    "RoleCompetenceRead",
    "RoleRead",
]

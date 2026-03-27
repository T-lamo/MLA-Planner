"""
Service de configuration des campus.

Permet au Super Admin de configurer entièrement l'application depuis le front
(ministères, catégories de rôles, rôles compétence, RBAC, statuts)
en remplacement du seed hardcodé.

Migrations DB requises avant activation complète :
  ALTER TABLE t_categorierole
    ADD COLUMN IF NOT EXISTS ministere_id VARCHAR
    REFERENCES t_ministere(id) ON DELETE SET NULL;
  ALTER TABLE t_categorierole
    ADD COLUMN IF NOT EXISTS description TEXT;
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, TypedDict

from sqlmodel import Session, col, select

from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
from mla_enum.custom_enum import (
    AffectationStatusCode,
    PlanningStatusCode,
    RoleName,
)
from models.campus_config_model import (
    CampusSetupPayload,
    CategorieSetupItem,
    MinistereSetupItem,
)
from models.schema_db_model import (
    Campus,
    CampusMinistereLink,
    CategorieRole,
    Ministere,
    Role,
    RoleCompetence,
    StatutAffectation,
    StatutPlanning,
)


class _SetupCounters(TypedDict):
    """Compteurs internes pour le setup campus."""

    ministeres_created: int
    ministeres_linked: int
    categories_created: int
    roles_created: int
    rbac_roles_created: int


class CampusConfigService:
    """Service de configuration du campus — sans héritage BaseService."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------ #
    #  HELPERS PRIVÉS
    # ------------------------------------------------------------------ #

    def _find_or_create_ministere(
        self,
        nom: str,
        description: Optional[str],
    ) -> Tuple[Ministere, bool]:
        """Recherche un ministère par nom, le crée si absent."""
        stmt = select(Ministere).where(Ministere.nom == nom)
        existing = self.db.exec(stmt).first()
        if existing:
            return existing, False
        new_min = Ministere(
            nom=nom,
            date_creation=datetime.now().strftime("%Y-%m-%d"),
            actif=True,
        )
        self.db.add(new_min)
        self.db.flush()
        self.db.refresh(new_min)
        return new_min, True

    def _find_or_create_categorie(
        self,
        nom: str,
        *,
        ministere_id: str,
        description: Optional[str] = None,
    ) -> Tuple[CategorieRole, bool]:
        """
        Cherche une catégorie par libellé + ministere_id.
        La crée si absente.
        """
        stmt = select(CategorieRole).where(
            CategorieRole.libelle == nom,
            CategorieRole.ministere_id == ministere_id,
        )
        existing = self.db.exec(stmt).first()
        if existing:
            return existing, False
        base = re.sub(r"[^A-Z0-9_]", "_", nom.strip().upper())[:20]
        code = base
        i = 1
        while self.db.get(CategorieRole, code) is not None:
            suffix = f"_{i}"
            code = base[: 20 - len(suffix)] + suffix
            i += 1
        new_cat = CategorieRole(
            code=code,
            libelle=nom,
            ministere_id=ministere_id,
            description=description,
        )
        self.db.add(new_cat)
        self.db.flush()
        self.db.refresh(new_cat)
        return new_cat, True

    def _find_or_create_role_competence(
        self,
        code: str,
        libelle: str,
        *,
        categorie_id: str,
        description: Optional[str] = None,
    ) -> Tuple[RoleCompetence, bool]:
        """
        Cherche un rôle compétence par code + catégorie.
        Lève CONF_ROLE_CODE_CONFLICT si le code existe dans une autre
        catégorie (les codes sont globalement uniques).
        """
        normalized = code.strip().upper()
        existing_global = self.db.get(RoleCompetence, normalized)
        if existing_global:
            if existing_global.categorie_code == categorie_id:
                return existing_global, False
            raise AppException(ErrorRegistry.CONF_ROLE_CODE_CONFLICT)
        new_role = RoleCompetence(
            code=normalized,
            libelle=libelle,
            categorie_code=categorie_id,
        )
        self.db.add(new_role)
        self.db.flush()
        self.db.refresh(new_role)
        return new_role, True

    def _find_or_create_rbac_role(
        self,
        libelle: str,
    ) -> Tuple[Role, bool]:
        """Cherche un rôle RBAC par libellé (str), le crée si absent."""
        stmt = select(Role).where(Role.libelle == libelle)
        existing = self.db.exec(stmt).first()
        if existing:
            return existing, False
        new_role = Role(libelle=libelle)
        self.db.add(new_role)
        self.db.flush()
        self.db.refresh(new_role)
        return new_role, True

    def _ensure_campus_ministere_link(
        self,
        campus_id: str,
        ministere_id: str,
    ) -> bool:
        """
        Vérifie si le lien campus-ministère existe.
        Le crée si absent. Retourne True si nouvellement créé.
        """
        stmt = select(CampusMinistereLink).where(
            CampusMinistereLink.campus_id == campus_id,
            CampusMinistereLink.ministere_id == ministere_id,
        )
        if self.db.exec(stmt).first():
            return False
        link = CampusMinistereLink(
            campus_id=campus_id,
            ministere_id=ministere_id,
        )
        self.db.add(link)
        self.db.flush()
        return True

    def _init_statut_planning(self) -> List[StatutPlanning]:
        """Initialise les statuts planning de façon idempotente."""
        result: List[StatutPlanning] = []
        for code in PlanningStatusCode:
            stmt = select(StatutPlanning).where(StatutPlanning.code == code.value)
            existing = self.db.exec(stmt).first()
            if existing:
                result.append(existing)
            else:
                sp = StatutPlanning(code=code.value)
                self.db.add(sp)
                self.db.flush()
                result.append(sp)
        return result

    def _init_statut_affectation(self) -> List[StatutAffectation]:
        """Initialise les statuts affectation de façon idempotente."""
        result: List[StatutAffectation] = []
        for code in AffectationStatusCode:
            stmt = select(StatutAffectation).where(StatutAffectation.code == code.value)
            existing = self.db.exec(stmt).first()
            if existing:
                result.append(existing)
            else:
                sa = StatutAffectation(
                    code=code.value,
                    libelle=code.value.capitalize(),
                )
                self.db.add(sa)
                self.db.flush()
                result.append(sa)
        return result

    # ------------------------------------------------------------------ #
    #  MÉTHODES PUBLIQUES — Statuts
    # ------------------------------------------------------------------ #

    def init_statuts(
        self,
    ) -> Tuple[List[StatutPlanning], List[StatutAffectation]]:
        """Initialise les statuts planning et affectation (idempotent)."""
        plannings = self._init_statut_planning()
        affectations = self._init_statut_affectation()
        return plannings, affectations

    # ------------------------------------------------------------------ #
    #  MÉTHODES PUBLIQUES — Campus
    # ------------------------------------------------------------------ #

    def list_campus(self) -> List[Campus]:
        """Liste tous les campus non supprimés."""
        stmt = select(Campus).where(Campus.deleted_at == None)  # noqa: E711
        return list(self.db.exec(stmt).all())

    # ------------------------------------------------------------------ #
    #  MÉTHODES PUBLIQUES — Ministères
    # ------------------------------------------------------------------ #

    def add_ministere_to_campus(
        self,
        campus_id: str,
        nom: str,
        *,
        description: Optional[str] = None,
    ) -> Tuple[Ministere, bool, bool]:
        """
        Ajoute un ministère à un campus.

        Retourne (ministere, created, linked) :
        - created=True si le ministère vient d'être créé
        - linked=True si le lien campus-ministère vient d'être créé
        """
        campus = self.db.get(Campus, campus_id)
        if not campus:
            raise AppException(ErrorRegistry.CONF_CAMPUS_NOT_FOUND)
        ministere, created = self._find_or_create_ministere(nom, description)
        linked = self._ensure_campus_ministere_link(campus_id, str(ministere.id))
        return ministere, created, linked

    def remove_ministere_from_campus(
        self,
        campus_id: str,
        ministere_id: str,
    ) -> None:
        """Supprime le lien campus-ministère sans supprimer l'entité."""
        stmt = select(CampusMinistereLink).where(
            CampusMinistereLink.campus_id == campus_id,
            CampusMinistereLink.ministere_id == ministere_id,
        )
        link = self.db.exec(stmt).first()
        if not link:
            raise AppException(ErrorRegistry.CONF_MINISTERE_LINK_NOT_FOUND)
        self.db.delete(link)
        self.db.flush()

    def list_all_ministeres(self) -> List[Ministere]:
        """Liste tous les ministères actifs du système (tous campus)."""
        stmt = select(Ministere).where(Ministere.deleted_at == None)  # noqa: E711
        return list(self.db.exec(stmt).all())

    def list_ministeres_of_campus(
        self,
        campus_id: str,
    ) -> List[Ministere]:
        """Liste les ministères liés à un campus."""
        campus = self.db.get(Campus, campus_id)
        if not campus:
            raise AppException(ErrorRegistry.CONF_CAMPUS_NOT_FOUND)
        stmt = (
            select(Ministere)
            .join(
                CampusMinistereLink,
                col(CampusMinistereLink.ministere_id) == col(Ministere.id),
            )
            .where(CampusMinistereLink.campus_id == campus_id)
            .where(Ministere.deleted_at == None)  # noqa: E711
        )
        return list(self.db.exec(stmt).all())

    # ------------------------------------------------------------------ #
    #  MÉTHODES PUBLIQUES — Catégories
    # ------------------------------------------------------------------ #

    def add_categorie_to_ministere(
        self,
        ministere_id: str,
        nom: str,
        *,
        description: Optional[str] = None,
    ) -> Tuple[CategorieRole, bool]:
        """Ajoute une catégorie à un ministère (find-or-create)."""
        ministere = self.db.get(Ministere, ministere_id)
        if not ministere:
            raise AppException(ErrorRegistry.MINST_NOT_FOUND, id=ministere_id)
        return self._find_or_create_categorie(
            nom,
            ministere_id=ministere_id,
            description=description,
        )

    def delete_categorie(
        self,
        ministere_id: str,
        categorie_id: str,
    ) -> None:
        """
        Supprime une catégorie si elle ne contient aucun rôle.
        Lève CONF_CATEGORIE_HAS_ROLES si des rôles y sont liés.
        """
        cat = self.db.get(CategorieRole, categorie_id)
        if not cat or cat.ministere_id != ministere_id:
            raise AppException(ErrorRegistry.ROLE_CAT_NOT_FOUND)
        count = len(cat.roles) if cat.roles else 0
        if count > 0:
            raise AppException(
                ErrorRegistry.CONF_CATEGORIE_HAS_ROLES,
                count=count,
            )
        self.db.delete(cat)
        self.db.flush()

    def list_categories_of_ministere(
        self,
        ministere_id: str,
    ) -> List[CategorieRole]:
        """Liste les catégories d'un ministère."""
        stmt = select(CategorieRole).where(CategorieRole.ministere_id == ministere_id)
        return list(self.db.exec(stmt).all())

    # ------------------------------------------------------------------ #
    #  MÉTHODES PUBLIQUES — Rôles Compétence
    # ------------------------------------------------------------------ #

    def add_role_competence_to_categorie(
        self,
        categorie_id: str,
        code: str,
        libelle: str,
        *,
        description: Optional[str] = None,
    ) -> Tuple[RoleCompetence, bool]:
        """Ajoute un rôle compétence à une catégorie (find-or-create)."""
        cat = self.db.get(CategorieRole, categorie_id)
        if not cat:
            raise AppException(ErrorRegistry.ROLE_CAT_NOT_FOUND)
        return self._find_or_create_role_competence(
            code,
            libelle,
            categorie_id=categorie_id,
            description=description,
        )

    def delete_role_competence(
        self,
        categorie_id: str,
        role_code: str,
    ) -> None:
        """
        Supprime un rôle compétence s'il n'est pas utilisé par des membres.
        Lève CONF_ROLE_IN_USE si des membres y sont liés.
        """
        normalized = role_code.strip().upper()
        stmt = select(RoleCompetence).where(
            RoleCompetence.code == normalized,
            RoleCompetence.categorie_code == categorie_id,
        )
        role = self.db.exec(stmt).first()
        if not role:
            raise AppException(
                ErrorRegistry.ROLE_NOT_FOUND,
                missing=normalized,
            )
        count = len(role.membres_assoc) if role.membres_assoc else 0
        if count > 0:
            raise AppException(
                ErrorRegistry.CONF_ROLE_IN_USE,
                count=count,
            )
        self.db.delete(role)
        self.db.flush()

    def link_role_competence_to_categorie(
        self,
        categorie_id: str,
        role_code: str,
    ) -> RoleCompetence:
        """
        Rattache un rôle compétence existant (autre catégorie) à cette
        catégorie en modifiant son categorie_code.
        """
        normalized = role_code.strip().upper()
        cat = self.db.get(CategorieRole, categorie_id)
        if not cat:
            raise AppException(ErrorRegistry.ROLE_CAT_NOT_FOUND)
        role = self.db.get(RoleCompetence, normalized)
        if not role:
            raise AppException(ErrorRegistry.ROLE_NOT_FOUND, missing=normalized)
        role.categorie_code = categorie_id
        self.db.add(role)
        self.db.flush()
        self.db.refresh(role)
        return role

    # ------------------------------------------------------------------ #
    #  MÉTHODES PUBLIQUES — Mises à jour
    # ------------------------------------------------------------------ #

    def update_ministere(
        self,
        ministere_id: str,
        *,
        nom: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Ministere:
        """Met à jour le nom et/ou la description d'un ministère."""
        min_ = self.db.get(Ministere, ministere_id)
        if not min_:
            raise AppException(ErrorRegistry.MINST_NOT_FOUND, id=ministere_id)
        if nom is not None:
            min_.nom = nom
        if description is not None:
            min_.description = description
        self.db.add(min_)
        self.db.flush()
        self.db.refresh(min_)
        return min_

    def update_categorie(
        self,
        ministere_id: str,
        categorie_id: str,
        *,
        nom: Optional[str] = None,
        description: Optional[str] = None,
    ) -> CategorieRole:
        """Met à jour le libellé et/ou la description d'une catégorie."""
        cat = self.db.get(CategorieRole, categorie_id)
        if not cat or cat.ministere_id != ministere_id:
            raise AppException(ErrorRegistry.ROLE_CAT_NOT_FOUND)
        if nom is not None:
            cat.libelle = nom
        if description is not None:
            cat.description = description
        self.db.add(cat)
        self.db.flush()
        self.db.refresh(cat)
        return cat

    def update_role_competence(
        self,
        categorie_id: str,
        role_code: str,
        *,
        libelle: Optional[str] = None,
        description: Optional[str] = None,
    ) -> RoleCompetence:
        """Met à jour le libellé et/ou la description d'un rôle compétence."""
        normalized = role_code.strip().upper()
        stmt = select(RoleCompetence).where(
            RoleCompetence.code == normalized,
            RoleCompetence.categorie_code == categorie_id,
        )
        role = self.db.exec(stmt).first()
        if not role:
            raise AppException(ErrorRegistry.ROLE_NOT_FOUND, missing=normalized)
        if libelle is not None:
            role.libelle = libelle
        if description is not None:
            role.description = description
        self.db.add(role)
        self.db.flush()
        self.db.refresh(role)
        return role

    # ------------------------------------------------------------------ #
    #  MÉTHODES PUBLIQUES — RBAC
    # ------------------------------------------------------------------ #

    def init_rbac_roles_for_ministere(
        self,
        campus_id: str,
        ministere_id: str,
    ) -> Tuple[List[Role], int]:
        """
        Initialise les 4 rôles RBAC standards (idempotent).

        Vérifie l'existence du campus et du lien campus-ministère,
        puis crée les rôles manquants.
        Retourne (roles, created_count).
        """
        campus = self.db.get(Campus, campus_id)
        if not campus:
            raise AppException(ErrorRegistry.CONF_CAMPUS_NOT_FOUND)
        link_stmt = select(CampusMinistereLink).where(
            CampusMinistereLink.campus_id == campus_id,
            CampusMinistereLink.ministere_id == ministere_id,
        )
        if not self.db.exec(link_stmt).first():
            raise AppException(ErrorRegistry.CONF_MINISTERE_LINK_NOT_FOUND)
        roles: List[Role] = []
        created_count = 0
        for role_name in [rn.value for rn in RoleName]:
            role, created = self._find_or_create_rbac_role(role_name)
            roles.append(role)
            if created:
                created_count += 1
        return roles, created_count

    # ------------------------------------------------------------------ #
    #  MÉTHODES PUBLIQUES — Résumé
    # ------------------------------------------------------------------ #

    def get_campus_summary(self, campus_id: str) -> Dict[str, Any]:
        """Retourne un résumé de la configuration d'un campus."""
        campus = self.db.get(Campus, campus_id)
        if not campus:
            raise AppException(ErrorRegistry.CONF_CAMPUS_NOT_FOUND)
        ministeres = self.list_ministeres_of_campus(campus_id)
        ministeres_data = self._build_ministeres_data(ministeres)
        sp_list = self._get_statut_planning_codes()
        sa_list = self._get_statut_affectation_codes()
        return {
            "campus_id": campus_id,
            "campus_nom": campus.nom,
            "ministeres": ministeres_data,
            "statuts_planning": sp_list,
            "statuts_affectation": sa_list,
        }

    def _build_ministeres_data(
        self,
        ministeres: List[Ministere],
    ) -> List[Dict[str, Any]]:
        """Construit la liste des ministères avec leurs catégories."""
        result: List[Dict[str, Any]] = []
        for ministere in ministeres:
            cats = self.list_categories_of_ministere(str(ministere.id))
            cats_data: List[Dict[str, Any]] = [
                {
                    "code": c.code,
                    "libelle": c.libelle,
                    "description": c.description,
                }
                for c in cats
            ]
            result.append(
                {
                    "id": str(ministere.id),
                    "nom": ministere.nom,
                    "description": getattr(ministere, "description", None),
                    "categories": cats_data,
                }
            )
        return result

    def _get_statut_planning_codes(self) -> List[str]:
        """Retourne les codes de statuts planning présents en DB."""
        stmt = select(StatutPlanning)
        return [sp.code for sp in self.db.exec(stmt).all()]

    def _get_statut_affectation_codes(self) -> List[str]:
        """Retourne les codes de statuts affectation présents en DB."""
        stmt = select(StatutAffectation)
        return [sa.code for sa in self.db.exec(stmt).all()]

    # ------------------------------------------------------------------ #
    #  SETUP COMPLET
    # ------------------------------------------------------------------ #

    def _setup_categorie_item(
        self,
        ministere_id: str,
        cat_item: CategorieSetupItem,
        counters: "_SetupCounters",
    ) -> None:
        """Configure une catégorie et ses rôles compétence."""
        cat, created = self._find_or_create_categorie(
            cat_item.nom,
            ministere_id=ministere_id,
            description=cat_item.description,
        )
        if created:
            counters["categories_created"] += 1
        for role_item in cat_item.roles:
            _, role_created = self._find_or_create_role_competence(
                role_item.code,
                role_item.libelle,
                categorie_id=cat.code,
                description=role_item.description,
            )
            if role_created:
                counters["roles_created"] += 1

    def _setup_ministere_item(
        self,
        campus_id: str,
        min_item: MinistereSetupItem,
        counters: "_SetupCounters",
    ) -> None:
        """Configure un ministère, ses catégories et optionnellement le RBAC."""
        min_obj, created = self._find_or_create_ministere(
            min_item.nom, min_item.description
        )
        if created:
            counters["ministeres_created"] += 1
        linked = self._ensure_campus_ministere_link(campus_id, str(min_obj.id))
        if linked:
            counters["ministeres_linked"] += 1
        for cat_item in min_item.categories:
            self._setup_categorie_item(str(min_obj.id), cat_item, counters)
        if min_item.init_rbac:
            _, rbac_count = self.init_rbac_roles_for_ministere(
                campus_id, str(min_obj.id)
            )
            counters["rbac_roles_created"] += rbac_count

    def setup_campus(
        self,
        campus_id: str,
        payload: CampusSetupPayload,
    ) -> Dict[str, Any]:
        """Configure un campus entièrement en une seule transaction."""
        campus = self.db.get(Campus, campus_id)
        if not campus:
            raise AppException(ErrorRegistry.CONF_CAMPUS_NOT_FOUND)
        counters: _SetupCounters = {
            "ministeres_created": 0,
            "ministeres_linked": 0,
            "categories_created": 0,
            "roles_created": 0,
            "rbac_roles_created": 0,
        }
        statuts_done = False
        if payload.init_statuts:
            self._init_statut_planning()
            self._init_statut_affectation()
            statuts_done = True
        for min_item in payload.ministeres:
            self._setup_ministere_item(campus_id, min_item, counters)
        return {
            "campus_id": campus_id,
            **counters,
            "statuts_initialises": statuts_done,
            "summary": self.get_campus_summary(campus_id),
        }

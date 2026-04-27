"""
Router admin — capabilities et permissions des rôles.

Préfixe : /admin
Accès : CAMPUS_ADMIN (lecture) / ROLE_MANAGE (écriture).
"""

from typing import Any, List, cast

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import selectinload
from sqlmodel import Session, delete, select

from conf.db.database import Database
from core.audit import audit
from core.auth.auth_dependencies import CasbinGuard, get_current_active_user
from core.auth.casbin_enforcer import build_enforcer
from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
from mla_enum import RoleName
from models import Utilisateur
from models.permission_model import (
    PermissionCodeRead,
    RoleCreate,
    RolePermissionsUpdate,
    RoleWithPermissionsRead,
)
from models.schema_db_model import (
    AffectationRole,
    Permission,
    Role,
    RolePermission,
)

router = APIRouter(prefix="/admin", tags=["Admin"])

_DB = Depends(Database.get_db_for_route)
_READ_GUARD = Depends(
    CasbinGuard("admin", "read", fallback_roles=["ADMIN", "SUPER_ADMIN", "DEMO"])
)
_WRITE_GUARD = Depends(
    CasbinGuard("admin", "write", fallback_roles=["ADMIN", "SUPER_ADMIN"])
)


_PROTECTED_ROLES = {RoleName.SUPER_ADMIN.value}

# Capabilities réservées au Super Admin — ne peuvent être attribuées via l'UI.
_PROTECTED_CAPABILITIES: set[str] = {"SYSTEM_MANAGE"}


def _assert_not_protected(role: Role) -> None:
    """Lève CORE_SYSTEM_ROLE_PROTECTED si le rôle est un rôle système."""
    if role.libelle in _PROTECTED_ROLES:
        raise AppException(ErrorRegistry.CORE_SYSTEM_ROLE_PROTECTED)


def _assert_no_protected_capabilities(codes: list[str]) -> None:
    """Lève CORE_SYSTEM_ROLE_PROTECTED si une capability système est demandée."""
    if _PROTECTED_CAPABILITIES & set(codes):
        raise AppException(ErrorRegistry.CORE_SYSTEM_ROLE_PROTECTED)


def _role_to_read(role: Role) -> RoleWithPermissionsRead:
    perms = [PermissionCodeRead(id=p.id, code=p.code) for p in role.permissions]
    return RoleWithPermissionsRead(
        id=role.id,
        libelle=role.libelle,
        permissions=perms,
    )


# ------------------------------------------------------------------ #
#  CAPABILITIES
# ------------------------------------------------------------------ #


@router.get(
    "/capabilities",
    response_model=List[PermissionCodeRead],
    status_code=status.HTTP_200_OK,
    summary="Lister toutes les capabilities disponibles",
    dependencies=[_READ_GUARD],
)
def list_capabilities(
    db: Session = _DB,
) -> List[PermissionCodeRead]:
    perms = db.exec(select(Permission).order_by(Permission.code)).all()
    return [PermissionCodeRead(id=p.id, code=p.code) for p in perms]


# ------------------------------------------------------------------ #
#  RÔLES + PERMISSIONS
# ------------------------------------------------------------------ #


@router.get(
    "/roles",
    response_model=List[RoleWithPermissionsRead],
    status_code=status.HTTP_200_OK,
    summary="Lister les rôles avec leurs permissions",
    dependencies=[_READ_GUARD],
)
def list_roles_with_permissions(
    db: Session = _DB,
) -> List[RoleWithPermissionsRead]:
    stmt = select(Role).options(selectinload(cast(Any, Role.permissions)))
    roles = db.exec(stmt).all()
    return [_role_to_read(r) for r in roles]


@router.post(
    "/roles",
    response_model=RoleWithPermissionsRead,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un nouveau rôle",
    dependencies=[_WRITE_GUARD],
)
def create_role(
    payload: RoleCreate,
    db: Session = _DB,
    current_user: Utilisateur = Depends(get_current_active_user),
) -> RoleWithPermissionsRead:
    if payload.libelle in _PROTECTED_ROLES:
        raise AppException(ErrorRegistry.CORE_SYSTEM_ROLE_PROTECTED)
    existing = db.exec(
        select(Role).where(cast(Any, Role.libelle) == payload.libelle)
    ).first()
    if existing:
        raise AppException(ErrorRegistry.CORE_RESOURCE_ALREADY_EXISTS)
    role = Role(libelle=payload.libelle)
    db.add(role)
    db.flush()
    db.refresh(role)
    audit("role_created", user_id=current_user.id, role_libelle=payload.libelle)
    return RoleWithPermissionsRead(id=role.id, libelle=role.libelle, permissions=[])


@router.delete(
    "/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un rôle (interdit s'il a des affectations)",
    dependencies=[_WRITE_GUARD],
)
def delete_role(
    role_id: str,
    db: Session = _DB,
    current_user: Utilisateur = Depends(get_current_active_user),
) -> None:
    role = db.get(Role, role_id)
    if not role:
        raise AppException(ErrorRegistry.CORE_RESOURCE_NOT_FOUND)
    _assert_not_protected(role)
    has_affectations = db.exec(
        select(AffectationRole).where(cast(Any, AffectationRole.role_id) == role_id)
    ).first()
    if has_affectations:
        raise AppException(ErrorRegistry.CORE_RESOURCE_IN_USE)
    audit(
        "role_deleted",
        user_id=current_user.id,
        role_id=role_id,
        role_libelle=role.libelle,
    )
    db.exec(  # type: ignore[call-overload]
        delete(RolePermission).where(cast(Any, RolePermission.role_id) == role_id)
    )
    db.delete(role)


@router.patch(
    "/roles/{role_id}/permissions",
    response_model=RoleWithPermissionsRead,
    status_code=status.HTTP_200_OK,
    summary="Remplacer les permissions d'un rôle",
    dependencies=[_WRITE_GUARD],
)
def update_role_permissions(
    role_id: str,
    payload: RolePermissionsUpdate,
    *,
    db: Session = _DB,
    current_user: Utilisateur = Depends(get_current_active_user),
) -> RoleWithPermissionsRead:
    role = db.get(Role, role_id)
    if not role:
        raise AppException(ErrorRegistry.CORE_RESOURCE_NOT_FOUND)
    _assert_not_protected(role)
    _assert_no_protected_capabilities(payload.permission_codes)

    db.exec(  # type: ignore[call-overload]
        delete(RolePermission).where(cast(Any, RolePermission.role_id) == role_id)
    )
    db.flush()

    perms = db.exec(
        select(Permission).where(
            cast(Any, Permission.code).in_(payload.permission_codes)
        )
    ).all()
    for perm in perms:
        db.add(RolePermission(role_id=role_id, permission_id=perm.id))
    db.flush()

    stmt = (
        select(Role)
        .where(Role.id == role_id)
        .options(selectinload(cast(Any, Role.permissions)))
    )
    updated = db.exec(stmt).first()
    if not updated:  # pragma: no cover
        raise AppException(ErrorRegistry.CORE_RESOURCE_NOT_FOUND)
    audit(
        "role_permissions_updated",
        user_id=current_user.id,
        role_id=role_id,
        permissions=",".join(payload.permission_codes),
    )
    build_enforcer(db)
    return _role_to_read(updated)

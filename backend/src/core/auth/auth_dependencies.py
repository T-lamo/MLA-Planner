# core/auth/auth_dependencies.py
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError as JWTError
from sqlmodel import Session, select

from conf.db.database import Database
from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
from core.settings import settings as stng
from mla_enum import RoleName
from models import Utilisateur
from models.schema_db_model import MembreCampusLink

from .auth_repository import AuthRepository
from .auth_utils import _affectation_valide, _role_name


def get_current_active_user(
    db: Session = Depends(Database.get_session),
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="/auth/token")),
) -> Utilisateur:
    try:
        # 1. Décodage du payload
        payload = jwt.decode(
            token, stng.JWT_SECRET_KEY, algorithms=[stng.JWT_ALGORITHM]
        )

        username = payload.get("sub")
        jti = payload.get("jti")  # <-- Nouvel identifiant du token

        # 2. Tes validations strictes sur le format du token
        if not isinstance(username, str) or username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide: sub manquant ou incorrect",
            )

        if not jti:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide: jti manquant",
            )

    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expirée ou corrompue",
        ) from exc

    repo = AuthRepository(db)

    # 3. VERIFICATION DE LA BLACKLIST (Logout)
    # On vérifie avant de charger l'utilisateur pour économiser une requête si révoqué
    if repo.is_token_revoked(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cette session a été fermée (déconnexion)",
        )

    # 4. Récupération de l'utilisateur
    user = repo.get_user_by_username(username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur introuvable"
        )

    # 5. Ta validation stricte du statut actif
    if not user.actif:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Utilisateur inactif"
        )

    # Astuce : On stocke le payload dans l'objet user pour que l'endpoint /logout
    # puisse y accéder sans avoir à redécoder le token.
    setattr(user, "_current_token_payload", payload)

    return user


class RoleChecker:
    """Vérifie si l'utilisateur possède un rôle actif et valide temporellement."""

    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(
        self, user: Utilisateur = Depends(get_current_active_user)
    ) -> list[str]:
        user_roles = [
            _role_name(aff.role.libelle)
            for aff in user.affectations
            if aff.role and aff.role.libelle is not None and _affectation_valide(aff)
        ]

        # Superadmin bypass — accès total sans restriction de rôle
        if RoleName.SUPER_ADMIN.name in user_roles:
            return user_roles

        if not any(role in self.allowed_roles for role in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Droits insuffisants pour cette action",
            )
        return user_roles


class ScopedRoleChecker:
    """Vérifie le rôle ET le scope ministère via AffectationContexte.

    - Affectation sans contexte → rôle global, accès accordé.
    - Affectation avec contextes → le ministere_id de la requête doit
      figurer dans la liste des contextes.
    - Super Admin → bypass total (rôle + scope).
    - ministere_id extrait de path_params puis query_params.
    - Absent de la requête → graceful skip du check de scope.
    """

    def __init__(self, allowed_roles: list[str]) -> None:
        self.allowed_roles = allowed_roles

    def __call__(
        self,
        request: Request,
        user: Utilisateur = Depends(get_current_active_user),
    ) -> list[str]:
        ministere_id: Optional[str] = request.path_params.get(
            "ministere_id"
        ) or request.query_params.get("ministere_id")

        granted: list[str] = []

        for aff in user.affectations:
            if not (aff.role and aff.role.libelle is not None):
                continue
            if not _affectation_valide(aff):
                continue

            role = _role_name(aff.role.libelle)

            if role == RoleName.SUPER_ADMIN.name:
                return [role]

            if role not in self.allowed_roles:
                continue

            if not aff.contextes:
                granted.append(role)
                continue

            if ministere_id is None or any(
                ctx.ministere_id == ministere_id for ctx in aff.contextes
            ):
                granted.append(role)

        if not granted:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Droits insuffisants pour cette action",
            )
        return granted


def _is_super_admin(user: Utilisateur) -> bool:
    """True si l'utilisateur possède un rôle Super Admin actif et valide."""
    return any(
        _role_name(aff.role.libelle) == RoleName.SUPER_ADMIN.name
        for aff in user.affectations
        if aff.role and aff.role.libelle is not None and _affectation_valide(aff)
    )


class CasbinGuard:
    """Vérifie les autorisations via le moteur Casbin (RBAC with domains).

    - obj : ressource (ex: "chants", "planning")
    - act : action (ex: "read", "write")
    - Si l'enforcer n'est pas encore initialisé, délègue à fallback_roles.
    - Super Admin : bypass total.
    - Domain résolu depuis path_params ou query_params (ministere_id).
    """

    def __init__(
        self,
        obj: str,
        act: str,
        *,
        fallback_roles: Optional[list[str]] = None,
    ) -> None:
        self.obj = obj
        self.act = act
        self._fallback = RoleChecker(fallback_roles or [])

    def __call__(
        self,
        request: Request,
        user: Utilisateur = Depends(get_current_active_user),
    ) -> list[str]:
        from .casbin_enforcer import (  # pylint: disable=import-outside-toplevel
            WILDCARD_DOMAIN,
            get_enforcer,
        )

        enf = get_enforcer()
        if enf is None:
            return self._fallback(user)

        if _is_super_admin(user):
            return [RoleName.SUPER_ADMIN.name]

        domain: str = (
            request.path_params.get("ministere_id")
            or request.query_params.get("ministere_id")
            or WILDCARD_DOMAIN
        )

        if not enf.enforce(user.id, domain, self.obj, self.act):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Droits insuffisants pour cette action",
            )
        return [user.id]


def get_active_campus(
    request: Request,
    db: Session = Depends(Database.get_session),
    user: Utilisateur = Depends(get_current_active_user),
) -> str:
    """Résout et valide le campus actif de la requête.

    Priorité : header X-Campus-Id > campus_principal_id du membre.
    Super Admin bypass le check d'appartenance.
    """
    campus_id: Optional[str] = request.headers.get("X-Campus-Id") or (
        user.membre.campus_principal_id if user.membre else None
    )
    if campus_id is None:
        raise AppException(ErrorRegistry.AUTH_CAMPUS_REQUIRED)
    if _is_super_admin(user):
        return campus_id
    if not user.membre_id:
        raise AppException(ErrorRegistry.AUTH_CAMPUS_FORBIDDEN)
    link = db.exec(
        select(MembreCampusLink)
        .where(MembreCampusLink.membre_id == user.membre_id)
        .where(MembreCampusLink.campus_id == campus_id)
    ).first()
    if not link:
        raise AppException(ErrorRegistry.AUTH_CAMPUS_FORBIDDEN)
    return campus_id

# core/auth/auth_dependencies.py
from enum import Enum

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError as JWTError
from sqlmodel import Session

from conf.db.database import Database
from core.settings import settings as stng
from mla_enum import RoleName
from models import Utilisateur

from .auth_repository import AuthRepository


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
    """Vérifie si l'utilisateur possède un rôle spécifique"""

    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(
        self, user: Utilisateur = Depends(get_current_active_user)
    ) -> list[str]:
        def _role_name(libelle: object) -> str:
            if isinstance(libelle, RoleName):
                return libelle.name  # "SUPER_ADMIN", "ADMIN", etc.
            if isinstance(libelle, Enum):
                return libelle.name
            return str(libelle)

        user_roles = [
            _role_name(aff.role.libelle)
            for aff in user.affectations
            if aff.role and aff.role.libelle is not None
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

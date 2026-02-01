# core/auth/auth_dependencies.py
from enum import Enum

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session

from conf.db.database import Database
from core.settings import settings as stng
from models import Utilisateur

from .auth_repository import AuthRepository


def get_current_active_user(
    db: Session = Depends(Database.get_session),
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="/auth/token")),
) -> Utilisateur:
    try:
        payload = jwt.decode(
            token, stng.JWT_SECRET_KEY, algorithms=[stng.JWT_ALGORITHM]
        )

        username = payload.get("sub")

        if not isinstance(username, str):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide: sub manquant",
            )

        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide"
            )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expirée"
        ) from exc

    repo = AuthRepository(db)
    user = repo.get_user_by_username(username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur introuvable"
        )

    # Validation stricte du statut actif en DB (pas seulement dans le token)
    if not user.actif:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Utilisateur inactif"
        )

    return user


class RoleChecker:
    """Vérifie si l'utilisateur possède un rôle spécifique"""

    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: Utilisateur = Depends(get_current_active_user)):
        # Conversion vers le nom de l'enum pour comparer avec allowed_roles
        user_roles = [
            (
                aff.role.libelle.name
                if isinstance(aff.role.libelle, Enum)
                else aff.role.libelle
            )
            for aff in user.affectations
            if aff.role
        ]

        print("allow role", self.allowed_roles)
        print("user role", user_roles)

        if not any(role in self.allowed_roles for role in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Droits insuffisants pour cette action",
            )
        return user_roles

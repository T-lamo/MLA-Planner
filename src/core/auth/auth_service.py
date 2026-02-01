# core/auth/auth_service.py
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlmodel import Session

from core.auth.auth_repository import AuthRepository
from core.auth.security import create_access_token, get_password_hash, verify_password
from models import Utilisateur


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AuthRepository(db)

    def _build_user_context(self, user: Utilisateur) -> List[Dict[str, Any]]:
        """Extrait les rôles et leurs contextes (Ministère, Pôle, Activite)"""
        contexts: List[Dict[str, Any]] = []

        for aff in user.affectations:
            role_code: Optional[str] = aff.role.libelle if aff.role else None
            permissions: List[str] = (
                [p.code for p in aff.role.permissions] if aff.role else []
            )

            role_info: Dict[str, Any] = {
                "role": role_code,
                "permissions": permissions,
                "scopes": [],
            }

            # Périmètres liés à cette affectation
            for ctx in aff.contextes:
                scope: Dict[str, Optional[str]] = {
                    "ministere_id": ctx.ministere_id,
                    "pole_id": ctx.pole_id,
                    "activite_id": ctx.activite_id,
                    "voix_id": getattr(ctx, "voix_id", None),
                }
                role_info["scopes"].append(scope)

            contexts.append(role_info)

        return contexts

    def authenticate_and_create_token(
        self, username: str, password: str
    ) -> Dict[str, Any]:
        user = self.repo.get_user_by_username(username)

        if not user or not verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Identifiants invalides",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.actif:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Compte désactivé",
            )

        token_data: Dict[str, Any] = {
            "sub": user.username,
            "user_id": user.id,
            "context": self._build_user_context(user),
        }

        token, expire = create_access_token(data=token_data)

        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_at": expire.isoformat(),
        }

    def change_password(
        self, utilisateur_id: str, current_password: str, new_password: str
    ) -> None:
        """
        Change le mot de passe d'un utilisateur après vérification.
        """
        # Si get_user_by_id attend un int, convertir si nécessaire
        try:
            user_id_int: int = int(utilisateur_id)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID utilisateur invalide",
            ) from exc

        user = self.repo.get_user_by_id(user_id_int)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utilisateur introuvable",
            )

        if not verify_password(current_password, user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le mot de passe actuel est incorrect",
            )

        hashed_new_password: str = get_password_hash(new_password)
        self.repo.update_password(user, hashed_new_password)

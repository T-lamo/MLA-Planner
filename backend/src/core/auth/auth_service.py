from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import jwt
from sqlmodel import Session

from core.audit import audit
from core.auth.auth_repository import AuthRepository
from core.auth.auth_utils import _affectation_valide
from core.auth.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    validate_password_strength,
    verify_password,
)
from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
from core.settings import settings as stng
from models import Utilisateur
from models.role_model import RoleRead
from models.utilisateur_model import UtilisateurRead


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

    def _build_capabilities(self, user: Utilisateur) -> List[str]:
        """Extrait la liste plate des codes de permission pour l'utilisateur."""
        caps: set[str] = set()
        for aff in user.affectations:
            if not _affectation_valide(aff):
                continue
            if aff.role:
                for perm in aff.role.permissions:
                    caps.add(perm.code)
        return sorted(caps)

    def _build_token_response(self, user: Utilisateur) -> Dict[str, Any]:
        """Émet access + refresh token et construit la réponse standard."""
        token_data: Dict[str, Any] = {
            "sub": user.username,
            "user_id": user.id,
            "context": self._build_user_context(user),
            "capabilities": self._build_capabilities(user),
        }
        token, expire = create_access_token(data=token_data)
        new_refresh = create_refresh_token(data={"sub": user.username})[0]

        campus_id = user.membre.campus_principal_id if user.membre else None
        name = (
            f"{user.membre.prenom} {user.membre.nom}" if user.membre else user.username
        )
        roles = [
            RoleRead(libelle=aff.role.libelle, id=aff.role.id)
            for aff in user.affectations
            if aff.role
        ]
        user_read = UtilisateurRead(
            id=user.id,
            username=user.username,
            actif=user.actif,
            membre_id=user.membre_id,
            campus_principal_id=campus_id,
            name=name,
            roles=roles,
            capabilities=self._build_capabilities(user),
        )
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_at": expire.isoformat(),
            "refresh_token": new_refresh,
            "user": user_read,
        }

    def authenticate_and_create_token(
        self, username: str, password: str
    ) -> Dict[str, Any]:
        user = self.repo.get_user_by_username(username)

        if not user or not verify_password(password, user.password):
            audit("login_failed", username=username)
            raise AppException(ErrorRegistry.AUTH_INVALID_CREDENTIALS)

        if not user.actif:
            audit("login_blocked", user_id=user.id, username=user.username)
            raise AppException(ErrorRegistry.AUTH_ACCOUNT_DISABLED)

        self.repo.purge_expired_tokens()
        audit("login", user_id=user.id, username=user.username)
        return self._build_token_response(user)

    def refresh_access_token(self, refresh_token_str: str) -> Dict[str, Any]:
        """Vérifie le refresh token, le blackliste, et émet une nouvelle paire."""
        try:
            payload = jwt.decode(
                refresh_token_str,
                stng.JWT_SECRET_KEY,
                algorithms=[stng.JWT_ALGORITHM],
            )
        except jwt.PyJWTError as exc:
            raise AppException(ErrorRegistry.AUTH_REFRESH_TOKEN_INVALID) from exc

        if payload.get("type") != "refresh":
            raise AppException(ErrorRegistry.AUTH_REFRESH_TOKEN_INVALID)

        jti = payload.get("jti")
        if not jti or self.repo.is_token_revoked(jti):
            raise AppException(ErrorRegistry.AUTH_REFRESH_TOKEN_INVALID)

        username = payload.get("sub")
        if not username:
            raise AppException(ErrorRegistry.AUTH_REFRESH_TOKEN_INVALID)

        user = self.repo.get_user_by_username(username)
        if not user or not user.actif:
            raise AppException(ErrorRegistry.AUTH_REFRESH_TOKEN_INVALID)

        # Rotation : blacklist de l'ancien refresh token
        exp_ts = payload.get("exp")
        if exp_ts:
            self.repo.add_to_blacklist(
                jti=jti,
                expires_at=datetime.fromtimestamp(exp_ts, tz=timezone.utc),
            )

        response = self._build_token_response(user)
        self.db.commit()
        return response

    def change_password(
        self, utilisateur_id: str, current_password: str, new_password: str
    ) -> None:
        """
        Change le mot de passe d'un utilisateur après vérification.
        """
        user = self.repo.get_user_by_id(utilisateur_id)

        if not user:
            raise AppException(ErrorRegistry.AUTH_USER_NOT_FOUND)

        if user.username == stng.DEMO_USERNAME:
            raise AppException(ErrorRegistry.AUTH_DEMO_READONLY)

        if not verify_password(current_password, user.password):
            raise AppException(ErrorRegistry.AUTH_CURRENT_PASSWORD_INCORRECT)

        validate_password_strength(new_password)
        hashed_new_password: str = get_password_hash(new_password)
        self.repo.update_password(user, hashed_new_password)
        self.db.commit()
        audit("password_changed", user_id=utilisateur_id)

    def logout(self, token_payload: dict) -> None:
        """
        Invalide un token en extrayant son JTI et sa date d'expiration.
        """
        jti = token_payload.get("jti")
        exp_timestamp = token_payload.get("exp")

        if not jti or not exp_timestamp:
            raise AppException(ErrorRegistry.AUTH_INVALID_LOGOUT_TOKEN)

        expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        self.repo.add_to_blacklist(jti=jti, expires_at=expires_at)
        self.db.commit()
        audit(
            "logout",
            user_id=token_payload.get("user_id"),
            username=token_payload.get("sub"),
        )

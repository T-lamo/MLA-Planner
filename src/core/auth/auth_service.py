from datetime import timedelta
from typing import Annotated

from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import constr
from sqlmodel import Session

from core.auth.auth_repository import AuthRepository
from core.auth.security import (
    create_access_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from core.exceptions import BadRequestException
from core.settings import settings as stng
from models import Utilisateur

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AuthRepository(db)

    # --- LOGIN / JWT ---
    def authenticate_user(self, username: str, password: str) -> Utilisateur | None:
        user = self.repo.get_user_by_username(username)
        if not user or not verify_password(password, user.password):
            return None
        return user

    def login_for_access_token(self, username: str, password: str) -> dict:
        user = self.authenticate_user(username, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=timedelta(minutes=stng.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        return {"access_token": access_token, "token_type": "bearer"}

    # --- CURRENT USER ---
    def get_current_user(self, token: str) -> Utilisateur:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = decode_token(token)
            username = payload.get("sub")
            if not username:
                raise credentials_exception
        except InvalidTokenError as exc:
            raise credentials_exception from exc

        user = self.repo.get_user_by_username(username)
        if not user:
            raise credentials_exception
        return user

    def get_current_active_user(self, token: str) -> Utilisateur:
        user = self.get_current_user(token)
        print(user)
        if not user.actif:
            raise HTTPException(status_code=400, detail="Inactive user")
        return user

    # --- CHANGE PASSWORD ---
    def change_password(
        self,
        utilisateur_id: int,
        current_password: str,
        new_password: Annotated[str, constr(min_length=6)],
    ) -> None:
        """
        Change le mot de passe d'un utilisateur.
        Vérifie le mot de passe actuel avant d'appliquer le nouveau.
        """
        user = self.repo.get_user_by_id(utilisateur_id)
        if not user:
            raise BadRequestException("Utilisateur introuvable")

        # Vérifier mot de passe actuel
        if not verify_password(current_password, user.password):
            raise BadRequestException("Mot de passe actuel incorrect")

        # Hash et update via le repo
        hashed = get_password_hash(new_password)
        self.repo.update_password(user, hashed)

    def authenticate_and_create_token(self, username, password):
        user = self.repo.get_user_by_username(username)

        # Le bloc que Pylint a repéré
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=timedelta(minutes=stng.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        return {"access_token": access_token, "token_type": "bearer"}

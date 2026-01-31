from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from conf.db.database import Database
from core.auth.auth_dependencies import get_current_active_user
from core.auth.auth_service import AuthService
from core.auth.models import PasswordChangeRequest, Token

router = APIRouter(prefix="/auth", tags=["auth"])


# ---------------------------
# Dépendance pour AuthService
# ---------------------------
def get_auth_service(db: Session = Depends(Database.get_session)) -> AuthService:
    return AuthService(db)


# ---------------------------
# LOGIN / TOKEN
# ---------------------------
@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
):
    return auth_service.authenticate_and_create_token(
        form_data.username, form_data.password
    )


@router.patch("/utilisateurs/{utilisateur_id}/password", status_code=status.HTTP_200_OK)
def change_password(
    utilisateur_id: int,
    passwords: PasswordChangeRequest,
    service: AuthService = Depends(get_auth_service),
):
    service.change_password(
        utilisateur_id,
        current_password=passwords.current_password,
        new_password=passwords.new_password,
    )
    return {"message": "Mot de passe mis à jour avec succès"}


# ---------------------------
# UTILISATEUR ACTIF
# ---------------------------
@router.get("/users/me")
async def read_users_me(current_user=Depends(get_current_active_user)):
    return current_user

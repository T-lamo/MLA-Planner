from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from conf.db.database import Database
from core.auth.auth_dependencies import RoleChecker, get_current_active_user
from core.auth.auth_service import AuthService
from core.auth.models import PasswordChangeRequest, Token
from models import Utilisateur

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
) -> Any:
    """
    Endpoint standard OAuth2 pour obtenir un token JWT.
    Le champ 'username' dans le formulaire correspond à l'identifiant technique.
    """
    return auth_service.authenticate_and_create_token(
        form_data.username, form_data.password
    )


# ---------------------------
# GESTION MOT DE PASSE
# ---------------------------
@router.patch("/utilisateurs/{utilisateur_id}/password", status_code=status.HTTP_200_OK)
def change_password(
    utilisateur_id: str,  # Changé en str car tes ID sont des UUID (max_length=36)
    passwords: PasswordChangeRequest,
    current_user: Utilisateur = Depends(get_current_active_user),
    service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    """
    Change le mot de passe d'un utilisateur.
    Sécurité : Un utilisateur ne peut modifier que son propre compte,
    sauf s'il possède le rôle ADMIN.
    """
    is_admin = any(
        aff.role.libelle == "ADMIN" for aff in current_user.affectations if aff.role
    )

    if current_user.id != utilisateur_id and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas l'autorisation de modifier ce mot de passe.",
        )

    service.change_password(
        utilisateur_id,
        current_password=passwords.current_password,
        new_password=passwords.new_password,
    )
    return {"message": "Mot de passe mis à jour avec succès"}


# ---------------------------
# UTILISATEUR ACTIF (ME)
# ---------------------------
@router.get(
    "/users/me", response_model=Any
)  # Tu peux créer un schéma UserRead plus tard
async def read_users_me(
    current_user: Utilisateur = Depends(get_current_active_user),
) -> Utilisateur:
    """
    Retourne les informations de l'utilisateur actuellement connecté
    extraites de la base de données via le token.
    """
    return current_user


# ---------------------------
# TEST RBAC (Exemple)
# ---------------------------
@router.get(
    "/admin-only", dependencies=[Depends(RoleChecker(["ADMIN", "RESPONSABLE_MLA"]))]
)
async def test_admin_route() -> dict[str, str]:
    """Route de test accessible uniquement aux administrateurs."""
    return {"message": "Bienvenue, Administrateur."}

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session

from conf.db.database import Database
from core.auth.auth_service import AuthService
from core.settings import settings as stng
from models import Utilisateur

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


## get current token for active user
def get_current_active_user(
    db: Session = Depends(Database.get_session), token: str = Depends(oauth2_scheme)
) -> Utilisateur:
    service = AuthService(db)
    return service.get_current_active_user(token)


def get_user_sub_from_token(token: str) -> str | None:
    """
    Extracts the 'sub' claim from a JWT token.
    Returns None if the token is invalid.
    """
    try:
        payload = jwt.decode(
            token,
            stng.JWT_SECRET_KEY,
            algorithms=[stng.JWT_ALGORITHM],
        )
        sub = payload.get("sub")
        return sub
    except JWTError:
        return None


# def require_admin_role(user: Utilisateur = Depends(get_current_active_user)):
#     pass
# Vérifier si l'utilisateur a le rôle ADMIN
# if any(role.libelle == RoleName.ADMIN for role in user.roles):
#     return user
# else:
#     raise ForbiddenException(detail="L'accès nécessite le rôle ADMIN.")

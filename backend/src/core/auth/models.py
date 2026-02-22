from typing import Annotated, Optional

from pydantic import BaseModel, constr
from sqlmodel import Field

from models.utilisateur_model import UtilisateurRead


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_at: str  # Ajouté pour le frontend
    refresh_token: Optional[str] = None
    user: Optional[UtilisateurRead]


class TokenData(BaseModel):
    username: str | None = None


class PasswordChangeRequest(BaseModel):
    current_password: Annotated[str, constr(min_length=6)]
    new_password: str = Field(min_length=6, max_length=128)

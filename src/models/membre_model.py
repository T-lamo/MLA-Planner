from typing import Optional

from sqlmodel import SQLModel

from .utilisateur_model import UtilisateurRead

# Base pour tous les modèles métier


class MembreBase(SQLModel):
    nom: str
    prenom: str
    email: Optional[str] = None
    telephone: Optional[str] = None
    actif: bool = True


# Create
class MembreCreate(MembreBase):
    ministere_id: str
    pole_id: str


# Read
class MembreRead(MembreBase):
    id: str
    dateInscription: Optional[str] = None
    ministere_id: str
    pole_id: str
    utilisateur: Optional["UtilisateurRead"] = None  # lecture sans mot de passe


# Update / Patch
class MembreUpdate(SQLModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None
    actif: Optional[bool] = None
    ministere_id: Optional[str] = None
    pole_id: Optional[str] = None


__all__ = ["MembreBase", "MembreCreate", "MembreRead", "MembreUpdate"]

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class PlanningNotification(BaseModel):
    """Schéma legacy — conservé pour ne pas casser le router existant."""

    email: EmailStr
    username: str
    shift_start: datetime
    shift_end: datetime
    location: str = "Site Principal"


class PlanningPublishedNotification(BaseModel):
    """Données d'une notification de publication pour un membre affecté."""

    email: EmailStr
    prenom: str
    nom: str
    type_activite: str
    date_activite: date
    heure_debut: str
    heure_fin: str
    lieu: Optional[str]
    campus_nom: str
    ministere_nom: str
    nom_creneau: str
    role_code: str


class PlanningCancelledNotification(BaseModel):
    """Données d'une notification d'annulation pour un membre affecté."""

    email: EmailStr
    prenom: str
    nom: str
    type_activite: str
    date_activite: date
    campus_nom: str
    ministere_nom: str
    motif: Optional[str] = None

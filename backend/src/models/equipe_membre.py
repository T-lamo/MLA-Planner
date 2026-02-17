# Dans ton fichier models/equipe_model.py (ou équivalent)


from models.membre_model import MembreRead  # Importe ton schéma membre existant
from sqlmodel import SQLModel


class EquipeMembreRead(SQLModel):
    """Schéma pour la table de liaison dans la réponse API"""

    membre: MembreRead  # C'est ici que le membre est exposé


__all__ = [
    "EquipeMembreRead",
]

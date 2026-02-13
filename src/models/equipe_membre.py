# Dans ton fichier models/equipe_model.py (ou équivalent)


from sqlmodel import SQLModel

from models.membre_model import MembreRead  # Importe ton schéma membre existant


class EquipeMembreRead(SQLModel):
    """Schéma pour la table de liaison dans la réponse API"""

    membre: MembreRead  # C'est ici que le membre est exposé


__all__ = [
    "EquipeMembreRead",
]

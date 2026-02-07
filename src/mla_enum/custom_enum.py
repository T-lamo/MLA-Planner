from enum import Enum


class RoleName(str, Enum):
    ADMIN = "Admin"
    RESPONSABLE_MLA = "Responsable MLA"
    MEMBRE_MLA = "Membre MLA"


class VoixEnum(str, Enum):
    SOPRANO = "SOPRANO"
    ALTO = "ALTO"
    TENOR = "TENOR"
    BARYTON = "BARYTON"
    BASSE = "BASSE"
    LEAD = "LEAD"


# 1. Définition des choix pour le niveau (Sécurité des données)
class NiveauChantre(str, Enum):
    DEBUTANT = "Débutant"
    INTERMEDIAIRE = "Intermédiaire"
    AVANCE = "Avancé"


__all__ = ["RoleName", "VoixEnum", "NiveauChantre"]

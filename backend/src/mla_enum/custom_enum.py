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


class PlanningStatusCode(str, Enum):
    BROUILLON = "BROUILLON"
    PUBLIE = "PUBLIE"
    ANNULE = "ANNULE"
    TERMINE = "TERMINE"


class AffectationStatusCode(str, Enum):
    PROPOSE = "PROPOSE"
    CONFIRME = "CONFIRME"
    REFUSE = "REFUSE"
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"


__all__ = [
    "RoleName",
    "VoixEnum",
    "NiveauChantre",
    "PlanningStatusCode",
    "AffectationStatusCode",
]

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


__all__ = ["RoleName", "VoixEnum"]

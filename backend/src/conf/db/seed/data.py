from datetime import datetime
from typing import List, TypedDict

from mla_enum import RoleName


# Définition des types pour Mypy
class MembreInfo(TypedDict):
    nom: str
    prenom: str
    email: str
    roles: List[str]


# --- RBAC ---
ROLES = [RoleName.ADMIN, RoleName.RESPONSABLE_MLA, RoleName.MEMBRE_MLA]

PERMISSIONS = {
    RoleName.ADMIN: [
        "USER_CREATE",
        "USER_READ",
        "USER_UPDATE",
        "USER_DELETE",
        "ROLE_MANAGE",
        "MINISTERE_MANAGE",
    ],
    RoleName.RESPONSABLE_MLA: [
        "USER_READ",
        "MINISTERE_MANAGE",
        "POLE_MANAGE",
        "ACTIVITE_MANAGE",
    ],
    RoleName.MEMBRE_MLA: ["USER_READ", "ACTIVITE_CREATE"],
}

# --- GEOGRAPHIE ---
# Ajout des dates de création et codes pays pour éviter les NotNullViolation
SEED_ORGANISATIONS = [{"nom": "ICC Europe", "date_creation": datetime(2010, 1, 1)}]
SEED_PAYS = [{"nom": "France", "code": "FR", "org_nom": "ICC Europe"}]
SEED_CAMPUS = [
    {
        "nom": "Campus Paris",
        "ville": "Paris",
        "timezone": "Europe/Paris",
        "pays_nom": "France",
    }
]

# --- NOUVEAU SCHÉMA MÉTIER ---
CATEGORIES_ROLES = [
    {"code": "VOIX", "libelle": "Pupitres Voix"},
    {"code": "INST", "libelle": "Instruments"},
    {"code": "TECH", "libelle": "Technique et Médias"},
]

ROLES_COMPETENCES = [
    {"code": "SOPRANO", "libelle": "Soprano", "cat": "VOIX"},
    {"code": "ALTO", "libelle": "Alto", "cat": "VOIX"},
    {"code": "TENOR", "libelle": "Ténor", "cat": "VOIX"},
    {"code": "PIANO", "libelle": "Piano", "cat": "INST"},
    {"code": "BATTERIE", "libelle": "Batterie", "cat": "INST"},
    {"code": "SON", "libelle": "Ingénieur Son", "cat": "TECH"},
]

MINISTERES_DATA = [
    {
        "nom": "Louange et Adoration",
        "date_creation": datetime(2020, 1, 1),
        "actif": True,
    },
    {"nom": "Enseignement", "date_creation": datetime(2021, 5, 10), "actif": True},
]

POLES_DATA = {
    "Louange et Adoration": [
        {"nom": "Chorale", "description": "Pôle voix", "active": True},
        {"nom": "Musiciens", "description": "Pôle instruments", "active": True},
    ],
    "Enseignement": [
        {"nom": "École du Dimanche", "description": "Enfants", "active": True}
    ],
}

STATUTS_PLANNING = ["BROUILLON", "PUBLIE", "ANNULE"]
TYPES_RESPONSABILITE = ["LEADER", "CO_LEADER", "ASSISTANT"]

ACTIVITES_DATA = [
    {"type": "Répétition", "lieu": "Salle A"},
    {"type": "Culte", "lieu": "Sanctuaire"},
]

EQUIPES_DATA = {"Louange et Adoration": ["Groupe de Louange A", "Groupe de Louange B"]}

MEMBRES_INFOS: List[MembreInfo] = [
    {
        "nom": "Dorceus",
        "prenom": "Amos",
        "email": "amos@exemple.com",
        "roles": ["TENOR", "PIANO"],
    },
    {
        "nom": "Dupont",
        "prenom": "Jean",
        "email": "jean.dupont@exemple.com",
        "roles": ["SON"],
    },
    {
        "nom": "Sow",
        "prenom": "Awa",
        "email": "awa.sow@exemple.com",
        "roles": ["SOPRANO"],
    },
    {
        "nom": "Lambert",
        "prenom": "Marie",
        "email": "marie.l@exemple.com",
        "roles": ["ALTO", "PIANO"],
    },
]

EQUIPE_MEMBRES_DATA = [
    {"equipe_nom": "Groupe de Louange A", "user_index": 0},
    {"equipe_nom": "Groupe de Louange A", "user_index": 2},
]

RESPONSABILITES_DATA = [
    {
        "user_index": 1,
        "type": "LEADER",
        "ministere": "Louange et Adoration",
        "pole": "Chorale",
    }
]

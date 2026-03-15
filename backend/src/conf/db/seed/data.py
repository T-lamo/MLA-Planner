from datetime import datetime
from typing import List, Optional, TypedDict

from mla_enum import RoleName


# Définition des types pour Mypy
class MembreInfo(TypedDict):
    nom: str
    prenom: str
    email: str
    roles: List[str]
    campus_names: Optional[List[str]]
    ministere_names: Optional[List[str]]
    pole_names: Optional[List[str]]


class ActiviteData(TypedDict):
    type: str
    lieu: str
    ministere_nom: str
    day_offset: int
    heure_debut: int
    heure_fin: int


class OrganisationData(TypedDict):
    nom: str
    date_creation: datetime


# --- RBAC ---
ROLES = [
    RoleName.SUPER_ADMIN,
    RoleName.ADMIN,
    RoleName.RESPONSABLE_MLA,
    RoleName.MEMBRE_MLA,
]

PERMISSIONS = {
    RoleName.SUPER_ADMIN: [
        "USER_CREATE",
        "USER_READ",
        "USER_UPDATE",
        "USER_DELETE",
        "ROLE_MANAGE",
        "MINISTERE_MANAGE",
        "POLE_MANAGE",
        "ACTIVITE_MANAGE",
        "SYSTEM_MANAGE",
    ],
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

# Compte superadmin fixe (ne doit jamais être lié à un membre)
SUPERADMIN_USERNAME = "superadmin"
SUPERADMIN_PASSWORD = "plan123!"

# Mot de passe commun pour tous les comptes non-superadmin
# Username = prenom.lower() du membre associé (ex: "amos", "jean", "awa")
USER_PASSWORD = "plan123!"

# --- GEOGRAPHIE ---
# Ajout des dates de création et codes pays pour éviter les NotNullViolation
SEED_ORGANISATIONS: List[OrganisationData] = [
    OrganisationData(nom="ICC Europe", date_creation=datetime(2010, 1, 1))
]
SEED_PAYS = [{"nom": "France", "code": "FR", "org_nom": "ICC Europe"}]
SEED_CAMPUS = [
    {
        "nom": "Campus Paris",
        "ville": "Paris",
        "timezone": "Europe/Paris",
        "pays_nom": "France",
    },
    {
        "nom": "Campus Toulouse",  # Nouveau Campus
        "ville": "Toulouse",
        "timezone": "Europe/Paris",
        "pays_nom": "France",
    },
]

# --- NOUVEAU SCHÉMA MÉTIER ---
CATEGORIES_ROLES = [
    {"code": "VOIX", "libelle": "Pupitres Voix"},
    {"code": "INST", "libelle": "Instruments"},
    {"code": "TECH", "libelle": "Technique et Médias"},
    {"code": "ACCUEIL", "libelle": "Accueil et Hospitalité"},
    {"code": "YOUTH", "libelle": "Jeunesse et Animation"},
]

ROLES_COMPETENCES = [
    {"code": "SOPRANO", "libelle": "Soprano", "cat": "VOIX"},
    {"code": "ALTO", "libelle": "Alto", "cat": "VOIX"},
    {"code": "TENOR", "libelle": "Ténor", "cat": "VOIX"},
    {"code": "PIANO", "libelle": "Piano", "cat": "INST"},
    {"code": "BATTERIE", "libelle": "Batterie", "cat": "INST"},
    {"code": "SON", "libelle": "Ingénieur Son", "cat": "TECH"},
    {"code": "LUMIERE", "libelle": "Technicien Lumière", "cat": "TECH"},
    {"code": "VIDEO", "libelle": "Opérateur Vidéo", "cat": "TECH"},
    {"code": "HOTE_ACCUEIL", "libelle": "Hôte d'Accueil", "cat": "ACCUEIL"},
    {"code": "ANIMATEUR_JEUNESSE", "libelle": "Animateur Jeunesse", "cat": "YOUTH"},
]

MINISTERES_DATA = [
    {
        "nom": "Louange et Adoration",
        "date_creation": datetime(2020, 1, 1),
        "actif": True,
    },
    {"nom": "Enseignement", "date_creation": datetime(2021, 5, 10), "actif": True},
    {"nom": "Technique", "date_creation": datetime(2021, 3, 1), "actif": True},
    {"nom": "Accueil", "date_creation": datetime(2022, 1, 15), "actif": True},
    {"nom": "Jeunesse", "date_creation": datetime(2022, 9, 1), "actif": True},
]

POLES_DATA = {
    "Louange et Adoration": [
        {"nom": "Chorale", "description": "Pôle voix", "active": True},
        {"nom": "Musiciens", "description": "Pôle instruments", "active": True},
    ],
    "Enseignement": [
        {"nom": "École du Dimanche", "description": "Enfants", "active": True}
    ],
    "Technique": [
        {
            "nom": "Son et Lumière",
            "description": "Régie son et éclairage",
            "active": True,
        },
        {
            "nom": "Vidéo et Streaming",
            "description": "Production vidéo",
            "active": True,
        },
    ],
    "Accueil": [
        {"nom": "Ushers", "description": "Accueil et placement", "active": True},
    ],
    "Jeunesse": [
        {"nom": "Ados", "description": "Groupe adolescents", "active": True},
    ],
}

STATUTS_PLANNING = ["BROUILLON", "PUBLIE", "ANNULE", "TERMINE"]
TYPES_RESPONSABILITE = ["LEADER", "CO_LEADER", "ASSISTANT"]

# 8 activités — une par planning, chacune liée à son ministère organisateur
# day_offset : jours depuis aujourd'hui ; heure_debut/fin :
# bornes de la journée
# complète
ACTIVITES_DATA: List[ActiviteData] = [
    {
        "type": "Culte Dominical",
        "lieu": "Sanctuaire",
        "ministere_nom": "Louange et Adoration",
        "day_offset": 7,
        "heure_debut": 9,
        "heure_fin": 21,
    },
    {
        "type": "Repetition Chorale",
        "lieu": "Salle A",
        "ministere_nom": "Louange et Adoration",
        "day_offset": 10,
        "heure_debut": 19,
        "heure_fin": 22,
    },
    {
        "type": "Second Culte Louange",
        "lieu": "Sanctuaire",
        "ministere_nom": "Louange et Adoration",
        "day_offset": 28,
        "heure_debut": 10,
        "heure_fin": 13,
    },
    # P8 — J+14 — distinct de J+7 pour tester get_member_agenda_full() sur 2 jours (C2)
    {
        "type": "Soiree Louange Mensuelle",
        "lieu": "Sanctuaire",
        "ministere_nom": "Louange et Adoration",
        "day_offset": 14,
        "heure_debut": 18,
        "heure_fin": 22,
    },
    {
        "type": "Service Technique Dim",
        "lieu": "Regie Son",
        "ministere_nom": "Technique",
        "day_offset": 7,
        "heure_debut": 8,
        "heure_fin": 21,
    },
    {
        "type": "Session Technique Form",
        "lieu": "Regie Lumiere",
        "ministere_nom": "Technique",
        "day_offset": 17,
        "heure_debut": 19,
        "heure_fin": 22,
    },
    {
        "type": "Permanence Accueil Culte",
        "lieu": "Hall Principal",
        "ministere_nom": "Accueil",
        "day_offset": 7,
        "heure_debut": 8,
        "heure_fin": 20,
    },
    {
        "type": "Reunion Jeunesse",
        "lieu": "Salle Jeunesse",
        "ministere_nom": "Jeunesse",
        "day_offset": 19,
        "heure_debut": 14,
        "heure_fin": 18,
    },
]

EQUIPES_DATA = {"Louange et Adoration": ["Groupe de Louange A", "Groupe de Louange B"]}

# 3 membres — aligné exactement sur les 3 users non-superadmin
# (ADMIN, RESPONSABLE_MLA, MEMBRE_MLA)
# u0 → Amos  : Louange et Adoration
# u1 → Jean  : Technique + Louange (son/lumière + chorale)
# u2 → Awa   : Accueil + Jeunesse (multi-ministère, couvre les 2 derniers plannings)
MEMBRES_INFOS: List[MembreInfo] = [
    {
        "nom": "Dorceus",
        "prenom": "Amos",
        "email": "amos@exemple.com",
        "roles": ["TENOR", "PIANO"],
        "campus_names": ["Campus Paris", "Campus Toulouse"],
        "ministere_names": ["Louange et Adoration"],
        "pole_names": ["Chorale", "Musiciens"],
    },
    {
        "nom": "Dupont",
        "prenom": "Jean",
        "email": "jean.dupont@exemple.com",
        "roles": ["SON", "LUMIERE", "VIDEO"],
        "campus_names": ["Campus Paris"],
        "ministere_names": ["Technique", "Louange et Adoration"],
        "pole_names": ["Son et Lumière", "Chorale"],
    },
    {
        "nom": "Sow",
        "prenom": "Awa",
        "email": "awa.sow@exemple.com",
        "roles": ["HOTE_ACCUEIL", "ANIMATEUR_JEUNESSE"],
        "campus_names": ["Campus Paris"],
        "ministere_names": ["Accueil", "Jeunesse"],
        "pole_names": ["Ushers", "Ados"],
    },
]

EQUIPE_MEMBRES_DATA = [
    {"equipe_nom": "Groupe de Louange A", "user_index": 0},  # Amos
    {"equipe_nom": "Groupe de Louange A", "user_index": 1},  # Jean
]

RESPONSABILITES_DATA = [
    {
        "user_index": 1,  # Jean — leader technique
        "type": "LEADER",
        "ministere": "Technique",
        "pole": "Son et Lumière",
    }
]

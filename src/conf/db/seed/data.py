from mla_enum import RoleName, VoixEnum

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
SEED_ORGANISATIONS = [{"nom": "ICC Europe", "date_creation": "2010-01-01"}]
SEED_PAYS = [{"nom": "France", "code": "FR", "org_nom": "ICC Europe"}]
SEED_CAMPUS = [
    {
        "nom": "Campus Paris",
        "ville": "Paris",
        "timezone": "Europe/Paris",
        "pays_nom": "France",
    }
]

# --- METIER ---
MINISTERES_DATA = [
    {"nom": "Louange et Adoration", "date_creation": "2020-01-01", "actif": True},
    {"nom": "Enseignement", "date_creation": "2021-05-10", "actif": True},
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

VOIX_DATA = [
    {"code": VoixEnum.SOPRANO, "nom": "Soprano"},
    {"code": VoixEnum.ALTO, "nom": "Alto"},
    {"code": VoixEnum.TENOR, "nom": "Ténor"},
    {"code": VoixEnum.BASSE, "nom": "Basse"},
]

INSTRUMENTS_DATA = ["Piano", "Batterie", "Guitare Basse", "Guitare Électrique"]
STATUTS_PLANNING = ["BROUILLON", "PUBLIE", "ANNULE"]
TYPES_RESPONSABILITE = ["LEADER", "CO_LEADER", "ASSISTANT"]

ACTIVITES_DATA = [
    {"type": "Répétition", "lieu": "Salle A", "description": "Répétition hebdo"},
    {"type": "Culte", "lieu": "Sanctuaire", "description": "Service Dimanche"},
]

EQUIPES_DATA = {"Louange et Adoration": ["Groupe de Louange A", "Groupe de Louange B"]}
# À ajouter dans data.py
MEMBRES_INFOS = [
    {"nom": "Dorceus", "prenom": "Amos", "email": "amos@exemple.com"},
    {"nom": "Dupont", "prenom": "Jean", "email": "jean.dupont@exemple.com"},
    {"nom": "Sow", "prenom": "Awa", "email": "awa.sow@exemple.com"},
    {"nom": "Lambert", "prenom": "Marie", "email": "marie.l@exemple.com"},
]

# Pour lier les membres aux équipes
EQUIPE_MEMBRES_DATA = [
    {"equipe_nom": "Groupe de Louange A", "user_index": 0},
    {"equipe_nom": "Groupe de Louange A", "user_index": 2},
]

# Pour assigner des responsabilités réelles
RESPONSABILITES_DATA = [
    {
        "user_index": 1,  # Le Responsable MLA
        "type": "LEADER",
        "ministere": "Louange et Adoration",
        "pole": "Chorale",
    }
]

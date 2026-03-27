from datetime import datetime
from typing import List, Optional, TypedDict


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


class PlanningTemplateRoleSeedData(TypedDict):
    role_code: str
    membres_suggeres_ids: List[str]


class PlanningTemplateSlotSeedData(TypedDict):
    nom_creneau: str
    offset_debut_minutes: int
    offset_fin_minutes: int
    nb_personnes_requis: int
    roles: List[PlanningTemplateRoleSeedData]


class PlanningTemplateSeedData(TypedDict):
    nom: str
    description: str
    activite_type: str
    duree_minutes: int
    ministere_nom: str
    slots: List[PlanningTemplateSlotSeedData]


# --- PLANNING TEMPLATES ---
PLANNING_TEMPLATES_SEED: List[PlanningTemplateSeedData] = [
    {
        "nom": "Culte Dominical Standard",
        "description": (
            "Template type pour un culte dominical" " avec louange matin et soir."
        ),
        "activite_type": "Culte Dominical",
        "duree_minutes": 720,
        "ministere_nom": "Louange et Adoration",
        "slots": [
            {
                "nom_creneau": "Équipe Louange Matin",
                "offset_debut_minutes": 0,
                "offset_fin_minutes": 180,
                "nb_personnes_requis": 2,
                "roles": [
                    {
                        "role_code": "TENOR",
                        "membres_suggeres_ids": [],
                    },
                    {
                        "role_code": "SON",
                        "membres_suggeres_ids": [],
                    },
                ],
            },
            {
                "nom_creneau": "Équipe Louange Soir",
                "offset_debut_minutes": 540,
                "offset_fin_minutes": 720,
                "nb_personnes_requis": 2,
                "roles": [
                    {
                        "role_code": "TENOR",
                        "membres_suggeres_ids": [],
                    },
                    {
                        "role_code": "SON",
                        "membres_suggeres_ids": [],
                    },
                ],
            },
        ],
    },
    {
        "nom": "Accueil Culte Standard",
        "description": "Template pour l'équipe d'accueil du culte.",
        "activite_type": "Culte Dominical",
        "duree_minutes": 720,
        "ministere_nom": "Accueil",
        "slots": [
            {
                "nom_creneau": "Accueil Entrée",
                "offset_debut_minutes": 0,
                "offset_fin_minutes": 60,
                "nb_personnes_requis": 3,
                "roles": [
                    {
                        "role_code": "HOTE_ACCUEIL",
                        "membres_suggeres_ids": [],
                    },
                ],
            },
        ],
    },
]


# --- RBAC ---
ROLES: list[str] = [
    "Super Admin",
    "Admin",
    "Responsable MLA",
    "Membre MLA",
]

PERMISSIONS: dict[str, list[str]] = {
    "Super Admin": [
        "USER_CREATE",
        "USER_READ",
        "USER_UPDATE",
        "USER_DELETE",
        "ROLE_MANAGE",
        "MINISTERE_MANAGE",
        "POLE_MANAGE",
        "ACTIVITE_MANAGE",
        "SYSTEM_MANAGE",
        "PLANNING_READ",
        "PLANNING_WRITE",
        "PLANNING_PUBLISH",
        "TEMPLATE_WRITE",
        "CHANT_READ",
        "CHANT_WRITE",
        "MEMBRE_READ",
        "MEMBRE_CREATE",
        "MEMBRE_UPDATE",
        "MEMBRE_DELETE",
        "INDISPO_WRITE",
        "CAMPUS_ADMIN",
    ],
    "Admin": [
        "USER_CREATE",
        "USER_READ",
        "USER_UPDATE",
        "USER_DELETE",
        "ROLE_MANAGE",
        "MINISTERE_MANAGE",
        "PLANNING_READ",
        "PLANNING_WRITE",
        "PLANNING_PUBLISH",
        "TEMPLATE_WRITE",
        "CHANT_READ",
        "CHANT_WRITE",
        "MEMBRE_READ",
        "MEMBRE_CREATE",
        "MEMBRE_UPDATE",
        "MEMBRE_DELETE",
        "INDISPO_WRITE",
        "CAMPUS_ADMIN",
    ],
    "Responsable MLA": [
        "USER_READ",
        "MINISTERE_MANAGE",
        "POLE_MANAGE",
        "ACTIVITE_MANAGE",
        "PLANNING_READ",
        "PLANNING_WRITE",
        "PLANNING_PUBLISH",
        "TEMPLATE_WRITE",
        "CHANT_READ",
        "CHANT_WRITE",
        "MEMBRE_READ",
        "MEMBRE_UPDATE",
        "INDISPO_WRITE",
    ],
    "Membre MLA": [
        "USER_READ",
        "ACTIVITE_CREATE",
        "PLANNING_READ",
        "CHANT_READ",
        "MEMBRE_READ",
    ],
}

# Ensemble canonique des capabilities de l'application.
# Source de vérité : toute capability utilisée dans un RoleChecker doit figurer ici.
# Les capabilities sont créées automatiquement au bootstrap (make db-setup-back).
# Ne jamais créer/supprimer via l'UI — modifier ce fichier + redéployer.
CAPABILITY_CODES: list[str] = [
    "ACTIVITE_CREATE",
    "ACTIVITE_MANAGE",
    "CAMPUS_ADMIN",
    "CHANT_READ",
    "CHANT_WRITE",
    "INDISPO_WRITE",
    "MEMBRE_CREATE",
    "MEMBRE_DELETE",
    "MEMBRE_READ",
    "MEMBRE_UPDATE",
    "MINISTERE_MANAGE",
    "PLANNING_PUBLISH",
    "PLANNING_READ",
    "PLANNING_WRITE",
    "POLE_MANAGE",
    "ROLE_MANAGE",
    "SYSTEM_MANAGE",
    "TEMPLATE_WRITE",
    "USER_CREATE",
    "USER_DELETE",
    "USER_READ",
    "USER_UPDATE",
]

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

# --- SONGBOOK ---


class ChantCategorieData(TypedDict):
    """Catégorie de chant à insérer en seed."""

    code: str
    libelle: str
    ordre: int


class ChantSeedData(TypedDict):
    """Chant + contenu ChordPro à insérer en seed."""

    titre: str
    artiste: str
    categorie_code: str
    tonalite: str
    paroles_chords: str
    youtube_url: Optional[str]


SONGBOOK_CATEGORIES: List[ChantCategorieData] = [
    {"code": "LOUANGE", "libelle": "Louange & Adoration", "ordre": 1},
    {"code": "CANTIQUES", "libelle": "Cantiques", "ordre": 2},
    {"code": "CONTEMPORAIN", "libelle": "Contemporain", "ordre": 3},
    {"code": "GOSPEL", "libelle": "Gospel", "ordre": 4},
    {"code": "TRADITIONNEL", "libelle": "Traditionnel", "ordre": 5},
]

SONGBOOK_CHANTS: List[ChantSeedData] = [
    {
        "titre": "Ma Source",
        "artiste": "ICC Worship",
        "categorie_code": "LOUANGE",
        "tonalite": "D",
        "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "paroles_chords": (
            "[D]Tu es ma sour-[A]ce, ma [Bm]force,\n"
            "[G]Tu es ma [D]vie. [A]\n"
            "[D]Je m'ap-pro-[A]che de [Bm]toi,\n"
            "[G]Mon [D]Dieu. [A] [D]\n"
            "\n"
            "[G]Dans ta pré-[D]sence, [A]je trouve la [D]paix.\n"
            "[G]Dans ton a-[Bm]mour, je suis [A]libé-[D]ré.\n"
            "[G]Je t'ho-[D]nore, [A]je te [D]loue,\n"
            "[G]Pour tou-[A]jours et à [D]jamais."
        ),
    },
    {
        "titre": "Je louerai l'Éternel",
        "artiste": "ICC Worship",
        "categorie_code": "LOUANGE",
        "tonalite": "C",
        "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "paroles_chords": (
            "[C]Je louerai l'É-[G]ternel de [Am]tout mon cœur,\n"
            "[F]Je raconterai [C]toutes tes [G]merveilles.\n"
            "[C]Je chanterai ton [G]nom, Dieu [Am]Très-Haut,\n"
            "[F]Car tu es [G]bon et miséri-[C]cordieux.\n"
            "\n"
            "[Am]Que toute [F]la terre [C]chante,\n"
            "[Am]Que toute [F]la terre [G]loue ton nom !\n"
            "[Am]Que toute [F]la terre [C]chante,\n"
            "[F]Gloire à [G]Dieu ! [C]"
        ),
    },
    {
        "titre": "Tu mérites",
        "artiste": "Hillsong FR",
        "categorie_code": "CONTEMPORAIN",
        "tonalite": "E",
        "youtube_url": None,
        "paroles_chords": (
            "[E]Tu mérites tout l'hon-[B]neur,\n"
            "[C#m]Tout l'honneur qui t'appar-[A]tient,\n"
            "[E]Tu mérites toute la [B]gloire,\n"
            "[C#m]Seigneur [A]Jésus. [E]\n"
            "\n"
            "[A]Hosan-[E]na ! Hosan-[B]na !\n"
            "[C#m]Hosanna au [A]Seigneur !\n"
            "[A]Hosan-[E]na ! Hosan-[B]na !\n"
            "[C#m]Seigneur [A]Jésus [B]Christ. [E]"
        ),
    },
    {
        "titre": "Splendeur de la Croix",
        "artiste": "Hillsong FR",
        "categorie_code": "CONTEMPORAIN",
        "tonalite": "A",
        "youtube_url": None,
        "paroles_chords": (
            "[A]Tu as été [E]percé pour [F#m]moi,\n"
            "[D]Tu as porté [A]ma [E]honte.\n"
            "[A]Sur la [E]croix, mon [F#m]Dieu, tu es [D]mort\n"
            "[A]Pour me donner la [E]vie. [A]\n"
            "\n"
            "[D]Splendeur de la [A]croix,\n"
            "[E]Grâce infi-[F#m]nie,\n"
            "[D]Ton sacri-[A]fice [E]m'a sau-[D]vé. [A]"
        ),
    },
    {
        "titre": "Alléluia",
        "artiste": "Gospel Chorale",
        "categorie_code": "GOSPEL",
        "tonalite": "F",
        "youtube_url": None,
        "paroles_chords": (
            "[F]Al-lé-lu-[Bb]ia, al-lé-lu-[C]ia,\n"
            "[F]Al-lé-lu-[Bb]ia, al-lé-lu-[C]ia. [F]\n"
            "\n"
            "[F]Gloire à [Bb]Dieu au plus haut des [C]cieux !\n"
            "[F]Il est vi-[Bb]vant, il est ressus-[C]ci-[F]té.\n"
            "[Dm]Son amour dure [Bb]à jamais,\n"
            "[C]Sa fidélité est éternel-[F]le."
        ),
    },
    {
        "titre": "Saint, Saint, Saint",
        "artiste": "Traditionnel",
        "categorie_code": "CANTIQUES",
        "tonalite": "G",
        "youtube_url": None,
        "paroles_chords": (
            "[G]Saint, [D]Saint, [Em]Saint !"
            " [C]Seigneur [G]Dieu [D]tout-puis-[G]sant !\n"
            "[Em]Toi qui é-[C]tais, qui [G]es\n"
            "[D]Et qui [G]viens.\n"
            "[C]Gloire et hon-[G]neur t'appar-[D]tiennent,\n"
            "[Em]Toi qui sièges [Am]sur le [C]trô-[D]ne.\n"
            "[C]À toi seul appar-[G]tient\n"
            "[D]La [C]gloire [G]éter-[D]nelle. [G]"
        ),
    },
    {
        "titre": "Quelle Grâce Étonnante",
        "artiste": "Traditionnel",
        "categorie_code": "TRADITIONNEL",
        "tonalite": "G",
        "youtube_url": None,
        "paroles_chords": (
            "[G]Quelle [C]grâce éton-[G]nante !\n"
            "[G]Quelle [D]merveille à mes [G]yeux !\n"
            "[G]Que l'a-[C]mour de Dieu, tendre et [G]grand,\n"
            "[D]M'ait sauvé du [G]gouffre.\n"
            "\n"
            "[G]J'étais per-[C]du, j'étais a-[G]veugle,\n"
            "[G]Mais mainte-[D]nant je [G]vois.\n"
            "[G]Sa grâce m'a [C]trouvé, et la-[G]vé,\n"
            "[D]Dans son précieux [G]sang."
        ),
    },
    {
        "titre": "Tu es Dieu",
        "artiste": "ICC Worship",
        "categorie_code": "LOUANGE",
        "tonalite": "Bb",
        "youtube_url": None,
        "paroles_chords": (
            "[Bb]Tu es [F]Dieu, tu es [Gm]Roi,\n"
            "[Eb]Tu règnes sur [Bb]tout. [F]\n"
            "[Bb]Tu es [F]saint, tu es [Gm]grand,\n"
            "[Eb]Seigneur de [F]seigneurs. [Bb]\n"
            "\n"
            "[Gm]Ton a-[Eb]mour est [Bb]éternel,\n"
            "[F]Ta parole est [Bb]vérité.\n"
            "[Gm]Nous t'a-[Eb]dorons, [Bb]ô [F]Dieu,\n"
            "[Eb]Nous t'hono-[F]rons. [Bb]"
        ),
    },
]

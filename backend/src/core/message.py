from dataclasses import dataclass

from fastapi import status


@dataclass(frozen=True)
class ErrorDetail:
    code: str
    message: str
    http_status: int


class ErrorRegistry:
    # --- DOMAINE PLANNING ---
    PLANNING_IMMUTABLE = ErrorDetail(
        code="PLAN_001",
        message="Le planning est {status}, modification interdite.",
        http_status=status.HTTP_400_BAD_REQUEST,
    )
    PLANNING_NOT_PUBLISHED = ErrorDetail(
        code="PLAN_002",
        message="Impossible de pointer sur un planning non publié.",
        http_status=status.HTTP_400_BAD_REQUEST,
    )
    PLANNING_NOT_FOUND = ErrorDetail(
        code="PLAN_003",
        message="Planning ou activité introuvable.",
        http_status=status.HTTP_400_BAD_REQUEST,
    )
    PLANNING_DELETE_IMPOSSIBLE = ErrorDetail(
        code="PLAN_004",
        message="Suppression impossible : le planning est {status}.",
        http_status=status.HTTP_400_BAD_REQUEST,
    )
    PLANNING_ACTIVITY_MISSING = ErrorDetail(
        code="PLAN_005",
        message="L'activité liée au planning est manquante.",
        http_status=status.HTTP_400_BAD_REQUEST,
    )
    PLANNING_DELETED_WITHOUT_ACTIVITY = ErrorDetail(
        code="PLAN_006",
        message="Planning {id} supprimé sans activité liée.",
        http_status=status.HTTP_200_OK,
    )
    PLANNING_FATAL_CREATION_ERROR = ErrorDetail(
        code="PLAN_007",
        message="Erreur fatale création planning complet : {error}",
        http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
    PLANNING_FATAL_UPDATE_ERROR = ErrorDetail(
        code="PLAN_008",
        message="Échec update complet Planning {id} : {error}",
        http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
    PLANNING_FATAL_DELETE_ERROR = ErrorDetail(
        code="PLAN_009",
        message="Échec du Full Delete {id}: {error}",
        http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
    # Nouveau : Context spécifique ValidationEngine (AC4)
    VALIDATION_PLANNING_NOT_FOUND = ErrorDetail(
        code="PLAN_010",
        message="Planning {id} non trouvé.",
        http_status=status.HTTP_404_NOT_FOUND,
    )

    PLAN_NOT_FOUND = ErrorDetail(
        code="PLAN_010",
        message="Le planning demandé est introuvable ou a été supprimé.",
        http_status=404,
    )

    PLANNING_CANT_PUBLISH = ErrorDetail(
        code="PLAN_012",
        message="Impossible de publier : aucun membre n'est affecté.",
        http_status=status.HTTP_400_BAD_REQUEST,
    )

    PLAN_013 = ErrorDetail(
        code="PLAN_013",
        message="Template de planning introuvable.",
        http_status=status.HTTP_404_NOT_FOUND,
    )
    PLAN_014 = ErrorDetail(
        code="PLAN_014",
        message=(
            "Impossible de créer un template : "
            "planning introuvable ou sans créneaux."
        ),
        http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )
    PLAN_015 = ErrorDetail(
        code="PLAN_015",
        message="Échec de la création du template de planning.",
        http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )

    # --- DOMAINE SLOT ---
    SLOT_OUT_OF_BOUNDS = ErrorDetail(
        code="SLOT_002",
        message="Le créneau doit être compris dans l'activité ({debut} - {fin}).",
        http_status=status.HTTP_400_BAD_REQUEST,
    )
    SLOT_CHRONOLOGY_ERROR = ErrorDetail(
        code="SLOT_003",
        message="La date de fin doit être après la date de début.",
        http_status=status.HTTP_400_BAD_REQUEST,
    )
    SLOT_NOT_FOUND = ErrorDetail(
        code="SLOT_004",
        message="Slot {id} introuvable.",
        http_status=status.HTTP_400_BAD_REQUEST,
    )
    # Nouveau : Context spécifique ValidationEngine (Timing AC1)
    VALIDATION_SLOT_OUT_OF_RANGE = ErrorDetail(
        code="SLOT_005",
        message="Le slot doit être compris entre {debut} et {fin}.",
        http_status=status.HTTP_400_BAD_REQUEST,
    )
    # --- DOMAINE Affectation (ASGN) ---
    Affectation_NOT_FOUND = ErrorDetail(
        code="ASGN_001",
        message="Affectation ou slot introuvable.",
        http_status=status.HTTP_400_BAD_REQUEST,
    )
    Affectation_PLANNING_NOT_FOUND = ErrorDetail(
        code="ASGN_002",
        message="Planning introuvable pour ce créneau.",
        http_status=status.HTTP_400_BAD_REQUEST,
    )
    Affectation_PLANNING_PARENT_MISSING = ErrorDetail(
        code="ASGN_003",
        message="Planning parent introuvable pour cette affectation.",
        http_status=status.HTTP_400_BAD_REQUEST,
    )
    Affectation_DATA_INCOMPLETE = ErrorDetail(
        code="ASGN_004",
        message="Données d'affectation incomplètes pour le slot {id}.",
        http_status=status.HTTP_200_OK,
    )
    # Nouveau : Context spécifique ValidationEngine (Vérification membre/slot)
    ASGN_SLOT_NOT_FOUND = ErrorDetail(
        code="ASGN_005",
        message="Slot {id} introuvable.",
        http_status=status.HTTP_404_NOT_FOUND,
    )
    ASGN_MEMBER_MISSING_ROLE = ErrorDetail(
        code="ASGN_006",
        message="Le membre ne possède pas le rôle requis : {role}.",
        http_status=status.HTTP_400_BAD_REQUEST,
    )
    AFFECTATION_TRANSITION_FORBIDDEN = ErrorDetail(
        code="ASGN_007",
        message="Transition de statut non autorisée pour ce rôle.",
        http_status=status.HTTP_403_FORBIDDEN,
    )
    AFFECTATION_NOT_OWNER = ErrorDetail(
        code="ASGN_008",
        message="Vous n'êtes pas le membre concerné par cette affectation.",
        http_status=status.HTTP_403_FORBIDDEN,
    )

    # --- DOMAINE WORKFLOW (WKFL) ---
    WORKFLOW_INVALID_TRANSITION = ErrorDetail(
        code="WKFL_001",
        message="Transition impossible: {current} -> {target}",
        http_status=status.HTTP_400_BAD_REQUEST,
    )
    WORKFLOW_HOOK_EXECUTION = ErrorDetail(
        code="WKFL_002",
        message="Exécution du hook pour transition {current} -> {target}",
        http_status=status.HTTP_200_OK,  # Utilisé pour logger.info
    )

    # --- DOMAINE ACTIVITÉ (ACTV) ---
    ACTV_TYPE_EMPTY = ErrorDetail(
        code="ACTV_001",
        message="Le type d'activité ne peut pas être vide.",
        http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
    ACTV_INVALID_CHRONOLOGY = ErrorDetail(
        code="ACTV_002",
        message="La date de fin doit être postérieure à la date de début.",
        http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
    ACTV_NOT_FOUND = ErrorDetail(
        code="ACTV_003",
        message="Activité {id} introuvable.",
        http_status=status.HTTP_404_NOT_FOUND,
    )

    # --- DOMAINE INDISPONIBILITÉ (INDISP) ---
    INDISP_INVALID_ISO_FORMAT = ErrorDetail(
        code="INDISP_001",
        message="Les dates doivent respecter le format YYYY-MM-DD.",
        http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
    INDISP_INVALID_CHRONOLOGY = ErrorDetail(
        code="INDISP_002",
        message=("La date de fin doit être postérieure ou égale à la date de début."),
        http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
    INDISP_ALREADY_VALIDATED = ErrorDetail(
        code="INDISP_003",
        message="Cette indisponibilité est déjà validée.",
        http_status=status.HTTP_409_CONFLICT,
    )
    INDISP_OVERLAP = ErrorDetail(
        code="INDISP_004",
        message="Une indisponibilité existe déjà pour cette période.",
        http_status=status.HTTP_409_CONFLICT,
    )
    INDISP_NOT_OWNER = ErrorDetail(
        code="INDISP_005",
        message="Vous ne pouvez pas modifier cette indisponibilité.",
        http_status=status.HTTP_403_FORBIDDEN,
    )
    INDISP_NOT_FOUND = ErrorDetail(
        code="INDISP_006",
        message="Indisponibilité introuvable.",
        http_status=status.HTTP_404_NOT_FOUND,
    )

    # --- DOMAINE CORE / GÉNÉRIQUE (CORE) ---

    CORE_RESOURCE_NOT_FOUND = ErrorDetail(
        code="CORE_001",
        message="{resource} introuvable.",
        http_status=status.HTTP_404_NOT_FOUND,
    )
    CORE_ACTION_IMPOSSIBLE = ErrorDetail(
        code="CORE_002",
        message="Action impossible sur {resource}.",
        http_status=status.HTTP_400_BAD_REQUEST,
    )

    # --- DOMAINE AUTHENTIFICATION (AUTH) ---
    AUTH_INVALID_CREDENTIALS = ErrorDetail(
        code="AUTH_001",
        message="Identifiants invalides.",
        http_status=status.HTTP_401_UNAUTHORIZED,
    )
    AUTH_ACCOUNT_DISABLED = ErrorDetail(
        code="AUTH_002",
        message="Compte désactivé.",
        http_status=status.HTTP_403_FORBIDDEN,
    )
    AUTH_USER_NOT_FOUND = ErrorDetail(
        code="AUTH_003",
        message="Utilisateur introuvable.",
        http_status=status.HTTP_404_NOT_FOUND,
    )
    AUTH_CURRENT_PASSWORD_INCORRECT = ErrorDetail(
        code="AUTH_004",
        message="Le mot de passe actuel est incorrect.",
        http_status=status.HTTP_400_BAD_REQUEST,
    )
    AUTH_INVALID_LOGOUT_TOKEN = ErrorDetail(
        code="AUTH_005",
        message="Token invalide pour la déconnexion.",
        http_status=status.HTTP_400_BAD_REQUEST,
    )
    AUTH_REFRESH_TOKEN_INVALID = ErrorDetail(
        code="AUTH_006",
        message="Token de rafraîchissement invalide ou expiré.",
        http_status=status.HTTP_401_UNAUTHORIZED,
    )

    # --- DOMAINE RÔLES ET CATÉGORIES (ROLE) ---
    ROLE_CAT_INVALID_CODE = ErrorDetail(
        code="ROLE_001",
        message="Le code doit être alphanumérique (underscores autorisés).",
        http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
    ROLE_NOT_FOUND = ErrorDetail(
        code="ROLE_002",
        message="Les rôles suivants sont introuvables : {missing}.",
        http_status=status.HTTP_404_NOT_FOUND,
    )

    # --- DOMAINE ÉQUIPE (TEAM) ---
    TEAM_NAME_EMPTY = ErrorDetail(
        code="TEAM_001",
        message="Le nom de l'équipe ne peut pas être vide.",
        http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
    TEAM_NOT_FOUND = ErrorDetail(
        code="TEAM_002",
        message="Équipe {id} introuvable.",
        http_status=status.HTTP_404_NOT_FOUND,
    )

    # --- DOMAINE MINISTÈRE (MINST) ---
    MINST_NAME_EMPTY = ErrorDetail(
        code="MINST_001",
        message="Le nom du ministère ne peut pas être vide.",
        http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
    MINST_NOT_FOUND = ErrorDetail(
        code="MINST_002",
        message="Ministère {id} introuvable.",
        http_status=status.HTTP_404_NOT_FOUND,
    )

    # --- DOMAINE MEMBRE ---
    MEMBRE_NOT_FOUND = ErrorDetail(
        code="MEMBRE_001",
        message="Le membre avec l'identifiant spécifié est introuvable.",
        http_status=status.HTTP_404_NOT_FOUND,
    )

    MEMBRE_CAMPUS_MISSING = ErrorDetail(
        code="MEMBRE_002",
        message="Le membre n'est rattaché à aucun campus, "
        "impossible de générer l'agenda.",
        http_status=status.HTTP_400_BAD_REQUEST,
    )

    # --- DOMAINE AGENDA ---
    AGENDA_DATA_ERROR = ErrorDetail(
        code="AGENDA_001",
        message="Erreur lors de la récupération des données de l'agenda.",
        http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )

    # --- DOMAINE PROFIL (PROF) ---

    PROFIL_DATA_ERROR = ErrorDetail(
        code="AGENDA_001",
        message="Erreur lors de la récupération des données de l'agenda.",
        http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )

    PROFIL_NOT_FOUND = ErrorDetail(
        code="PROF_001",
        message="Le profil {id} est introuvable.",
        http_status=status.HTTP_404_NOT_FOUND,
    )
    PROFIL_USER_LINK_MISSING = ErrorDetail(
        code="PROF_002",
        message="L'utilisateur associé au profil est introuvable.",
        http_status=status.HTTP_404_NOT_FOUND,
    )
    PROFIL_ALREADY_EXISTS = ErrorDetail(
        code="PROF_003",
        message="Un profil avec cet email existe déjà.",
        http_status=status.HTTP_409_CONFLICT,
    )
    PROFIL_CAMPUS_PRINCIPAL_INVALID = ErrorDetail(
        code="PROF_004",
        message="Le campus principal doit être parmi les campus affectés au membre.",
        http_status=status.HTTP_400_BAD_REQUEST,
    )

    # --- DOMAINE CORE / GÉNÉRIQUE (CORE) ---
    CORE_RESOURCE_NOT_FOUND = ErrorDetail(
        code="CORE_001",
        message="{resource} introuvable.",
        http_status=status.HTTP_404_NOT_FOUND,
    )
    CORE_ACTION_IMPOSSIBLE = ErrorDetail(
        code="CORE_002",
        message="Action impossible sur {resource}.",
        http_status=status.HTTP_400_BAD_REQUEST,
    )
    CORE_DATABASE_ERROR = ErrorDetail(
        code="CORE_003",
        message="Une erreur inattendue est survenue au niveau de la base de données.",
        http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
    CORE_INTEGRITY_ERROR = ErrorDetail(
        code="CORE_004",
        message="Erreur d'intégrité lors de l'opération.",
        http_status=status.HTTP_400_BAD_REQUEST,
    )
    CORE_DUPLICATE = ErrorDetail(
        code="CORE_005",
        message="{resource} avec ce code ou ce nom existe déjà.",
        http_status=status.HTTP_409_CONFLICT,
    )

    # --- DOMAINE CAMPUS (CAMP) ---
    CAMP_NOT_FOUND = ErrorDetail(
        code="CAMP_001",
        message="Campus {id} introuvable.",
        http_status=status.HTTP_404_NOT_FOUND,
    )
    CAMP_LINK_ERROR = ErrorDetail(
        code="CAMP_002",
        message="Impossible de mettre à jour les liaisons ministères.",
        http_status=status.HTTP_400_BAD_REQUEST,
    )

    # --- DOMAINE PAYS (PAYS) ---
    PAYS_NOT_FOUND = ErrorDetail(
        code="PAYS_001",
        message="Pays introuvable.",
        http_status=status.HTTP_404_NOT_FOUND,
    )
    PAYS_DUPLICATE = ErrorDetail(
        code="PAYS_002",
        message="Le pays ou son code existe déjà.",
        http_status=status.HTTP_409_CONFLICT,
    )

    # --- DOMAINE ORGANISATION (ORG) ---
    ORG_NOT_FOUND = ErrorDetail(
        code="ORG_001",
        message="Organisation introuvable.",
        http_status=status.HTTP_404_NOT_FOUND,
    )
    ORG_DUPLICATE = ErrorDetail(
        code="ORG_002",
        message="L'organisation '{nom}' existe déjà.",
        http_status=status.HTTP_409_CONFLICT,
    )

    # --- DOMAINE MINISTÈRE (MINST) compléments ---
    MINST_DUPLICATE = ErrorDetail(
        code="MINST_003",
        message="Le ministère '{nom}' existe déjà dans l'organisation.",
        http_status=status.HTTP_400_BAD_REQUEST,
    )
    MINST_CAMPUS_REQUIRED = ErrorDetail(
        code="MINST_004",
        message="Un ministère doit être lié à au moins un campus.",
        http_status=status.HTTP_400_BAD_REQUEST,
    )

    # --- DOMAINE PÔLE (POLE) ---
    POLE_NOT_FOUND = ErrorDetail(
        code="POLE_001",
        message="Pôle introuvable.",
        http_status=status.HTTP_404_NOT_FOUND,
    )
    POLE_DUPLICATE = ErrorDetail(
        code="POLE_002",
        message="Un pôle avec ce nom existe déjà.",
        http_status=status.HTTP_409_CONFLICT,
    )

    # --- DOMAINE MEMBRE compléments ---
    MEMBRE_CAMPUS_REQUIRED = ErrorDetail(
        code="MEMBRE_003",
        message="Un membre doit être rattaché à au moins un campus.",
        http_status=status.HTTP_400_BAD_REQUEST,
    )
    MEMBRE_DELETED = ErrorDetail(
        code="MEMBRE_004",
        message="Impossible de modifier un membre supprimé.",
        http_status=status.HTTP_400_BAD_REQUEST,
    )
    MEMBRE_ALREADY_LINKED = ErrorDetail(
        code="MEMBRE_005",
        message="Ce membre est déjà lié à un compte utilisateur.",
        http_status=status.HTTP_409_CONFLICT,
    )
    USER_ALREADY_LINKED = ErrorDetail(
        code="MEMBRE_006",
        message="Cet utilisateur est déjà lié à un membre.",
        http_status=status.HTTP_409_CONFLICT,
    )
    MEMBRE_ROLE_DUPLICATE = ErrorDetail(
        code="MEMBRE_007",
        message="Ce membre possède déjà ce rôle.",
        http_status=status.HTTP_409_CONFLICT,
    )
    MEMBRE_ROLE_NOT_FOUND = ErrorDetail(
        code="MEMBRE_008",
        message="Affectation membre/rôle introuvable.",
        http_status=status.HTTP_404_NOT_FOUND,
    )

    # --- DOMAINE RÔLES ET CATÉGORIES compléments ---
    ROLE_CAT_NOT_FOUND = ErrorDetail(
        code="ROLE_003",
        message="Catégorie de rôle introuvable.",
        http_status=status.HTTP_404_NOT_FOUND,
    )
    ROLE_CAT_DUPLICATE = ErrorDetail(
        code="ROLE_004",
        message="Le code '{code}' est déjà utilisé.",
        http_status=status.HTTP_409_CONFLICT,
    )
    ROLE_COMP_DUPLICATE = ErrorDetail(
        code="ROLE_005",
        message="Le rôle avec le code '{code}' existe déjà.",
        http_status=status.HTTP_409_CONFLICT,
    )

    # --- DOMAINE ÉQUIPE compléments ---
    TEAM_MEMBER_DUPLICATE = ErrorDetail(
        code="TEAM_003",
        message="Ce membre est déjà dans cette équipe.",
        http_status=status.HTTP_409_CONFLICT,
    )
    TEAM_MEMBER_NOT_FOUND = ErrorDetail(
        code="TEAM_004",
        message="Le membre ne fait pas partie de cette équipe.",
        http_status=status.HTTP_404_NOT_FOUND,
    )

    # --- DOMAINE ACTIVITÉ compléments ---
    ACTV_INVALID_REF = ErrorDetail(
        code="ACTV_004",
        message="Données de référence (Campus/Ministère) invalides.",
        http_status=status.HTTP_400_BAD_REQUEST,
    )
    ACTV_UPDATE_CONFLICT = ErrorDetail(
        code="ACTV_005",
        message="Erreur de contrainte lors de la mise à jour.",
        http_status=status.HTTP_409_CONFLICT,
    )

    # --- DOMAINE CONFIGURATION CAMPUS (CONF) ---
    CONF_CAMPUS_NOT_FOUND = ErrorDetail(
        code="CONF_001",
        message="Campus introuvable.",
        http_status=status.HTTP_404_NOT_FOUND,
    )
    CONF_MINISTERE_LINK_EXISTS = ErrorDetail(
        code="CONF_002",
        message="Ce ministère est déjà lié à ce campus.",
        http_status=status.HTTP_409_CONFLICT,
    )
    CONF_MINISTERE_LINK_NOT_FOUND = ErrorDetail(
        code="CONF_003",
        message="Lien campus-ministère introuvable.",
        http_status=status.HTTP_404_NOT_FOUND,
    )
    CONF_ROLE_CODE_CONFLICT = ErrorDetail(
        code="CONF_004",
        message="Le code {code} existe déjà dans une autre catégorie.",
        http_status=status.HTTP_409_CONFLICT,
    )
    CONF_ROLE_IN_USE = ErrorDetail(
        code="CONF_005",
        message="Ce rôle est utilisé par {count} membre(s), suppression impossible.",
        http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )
    CONF_CATEGORIE_HAS_ROLES = ErrorDetail(
        code="CONF_006",
        message=("Cette catégorie contient {count} rôle(s), suppression impossible."),
        http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )

    # --- DOMAINE CHANTS / SONGBOOK (SONG) ---
    SONG_CAT_NOT_FOUND = ErrorDetail(
        code="SONG_001",
        message="Catégorie de chant introuvable.",
        http_status=status.HTTP_404_NOT_FOUND,
    )
    SONG_CAT_DUPLICATE = ErrorDetail(
        code="SONG_002",
        message="Une catégorie avec ce code existe déjà.",
        http_status=status.HTTP_409_CONFLICT,
    )
    SONG_CAT_HAS_CHANTS = ErrorDetail(
        code="SONG_003",
        message=("Cette catégorie contient {count} chant(s), suppression impossible."),
        http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )
    SONG_NOT_FOUND = ErrorDetail(
        code="SONG_004",
        message="Chant introuvable.",
        http_status=status.HTTP_404_NOT_FOUND,
    )
    SONG_DELETED = ErrorDetail(
        code="SONG_005",
        message="Impossible de modifier un chant supprimé.",
        http_status=status.HTTP_400_BAD_REQUEST,
    )
    SONG_CONTENT_VERSION_CONFLICT = ErrorDetail(
        code="SONG_006",
        message=("Conflit de version : version attendue {expected}, reçue {received}."),
        http_status=status.HTTP_409_CONFLICT,
    )
    SONG_INVALID_SEMITONES = ErrorDetail(
        code="SONG_007",
        message="Les demi-tons doivent être compris entre -12 et 12.",
        http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )

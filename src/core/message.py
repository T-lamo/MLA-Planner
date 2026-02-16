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

    # --- DOMAINE SLOT ---
    SLOT_COLLISION = ErrorDetail(
        code="SLOT_001",
        message="Collision avec le créneau existant : '{nom}'.",
        http_status=status.HTTP_409_CONFLICT,
    )
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
    # Nouveau : Context spécifique ValidationEngine (Collision AC3 avec détails)
    VALIDATION_SLOT_COLLISION_DETAIL = ErrorDetail(
        code="SLOT_006",
        message="Collision avec le slot existant '{nom}' ({debut} - {fin}).",
        http_status=status.HTTP_409_CONFLICT,
    )

    # --- DOMAINE ASSIGNMENT (ASGN) ---
    ASSIGNMENT_NOT_FOUND = ErrorDetail(
        code="ASGN_001",
        message="Affectation ou slot introuvable.",
        http_status=status.HTTP_400_BAD_REQUEST,
    )
    ASSIGNMENT_PLANNING_NOT_FOUND = ErrorDetail(
        code="ASGN_002",
        message="Planning introuvable pour ce créneau.",
        http_status=status.HTTP_400_BAD_REQUEST,
    )
    ASSIGNMENT_PLANNING_PARENT_MISSING = ErrorDetail(
        code="ASGN_003",
        message="Planning parent introuvable pour cette affectation.",
        http_status=status.HTTP_400_BAD_REQUEST,
    )
    ASSIGNMENT_DATA_INCOMPLETE = ErrorDetail(
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
        message="La date de fin doit être postérieure ou égale à la date de début.",
        http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
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

    # --- DOMAINE RÔLES ET CATÉGORIES (ROLE) ---
    ROLE_CAT_INVALID_CODE = ErrorDetail(
        code="ROLE_001",
        message="Le code doit être alphanumérique (underscores autorisés).",
        http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
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

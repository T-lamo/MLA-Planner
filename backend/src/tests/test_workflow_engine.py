from unittest.mock import MagicMock

import pytest

from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
from mla_enum.custom_enum import AffectationStatusCode, PlanningStatusCode

# -----------------------------------------------------------------------------
# FIXTURES
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# TESTS : VALIDATION & TRANSITIONS
# -----------------------------------------------------------------------------


def test_validate_transition_success(planning_wf):
    """Vérifie qu'une transition autorisée ne lève aucune exception."""
    # Passage standard : BROUILLON -> PUBLIE
    try:
        planning_wf.validate_transition(
            PlanningStatusCode.BROUILLON, PlanningStatusCode.PUBLIE
        )
    except AppException:
        pytest.fail(
            "validate_transition a levé AppException sur une transition valide."
        )


def test_validate_transition_failure(planning_wf):
    """Vérifie qu'une transition interdite lève
    AppException avec les bons métadonnées."""
    with pytest.raises(AppException) as excinfo:
        # Passage interdit : BROUILLON -> TERMINE
        planning_wf.validate_transition(
            PlanningStatusCode.BROUILLON, PlanningStatusCode.TERMINE
        )

    # Vérification de l'erreur via l'objet ErrorDetail
    assert excinfo.value.detail == ErrorRegistry.WORKFLOW_INVALID_TRANSITION

    # On vérifie que le message contient les valeurs injectées
    # (formatées par AppException)
    assert PlanningStatusCode.BROUILLON.value in excinfo.value.message
    assert PlanningStatusCode.TERMINE.value in excinfo.value.message


def test_robustness_with_string_input(planning_wf):
    """Vérifie que le moteur accepte des strings au lieu des Enums (normalisation)."""
    # On simule l'arrivée d'une string depuis une requête API
    try:
        planning_wf.validate_transition("BROUILLON", "PUBLIE")
    except AppException:
        pytest.fail("Le moteur n'a pas réussi à normaliser l'entrée string.")


# -----------------------------------------------------------------------------
# TESTS : EXECUTION & HOOKS
# -----------------------------------------------------------------------------


def test_execute_transition_with_hook_success(planning_wf):
    """Vérifie que le hook est bien exécuté lors d'une transition valide."""
    mock_hook = MagicMock()

    planning_wf.execute_transition(
        PlanningStatusCode.BROUILLON, PlanningStatusCode.PUBLIE, hook=mock_hook
    )

    mock_hook.assert_called_once()


def test_execute_transition_interrupted_hook(planning_wf):
    """Vérifie que le hook n'est jamais appelé si la validation échoue."""
    mock_hook = MagicMock()

    with pytest.raises(AppException):
        planning_wf.execute_transition(
            PlanningStatusCode.BROUILLON, PlanningStatusCode.TERMINE, hook=mock_hook
        )

    mock_hook.assert_not_called()


# -----------------------------------------------------------------------------
# TESTS : LECTURE DES POSSIBLES (GET_ALLOWED)
# -----------------------------------------------------------------------------


def test_get_allowed_transitions_standard(affectation_wf):
    """Vérifie la récupération des transitions pour un état non-terminal."""
    allowed = affectation_wf.get_allowed_transitions(AffectationStatusCode.CONFIRME)

    expected = [
        AffectationStatusCode.PRESENT,
        AffectationStatusCode.ABSENT,
        AffectationStatusCode.REFUSE,
    ]
    assert allowed == expected


def test_get_allowed_transitions_terminal(planning_wf):
    """Vérifie qu'un état terminal (TERMINE) retourne une liste vide."""
    allowed = planning_wf.get_allowed_transitions(PlanningStatusCode.TERMINE)
    assert allowed == []


def test_get_allowed_transitions_unknown(planning_wf, caplog):
    """Vérifie le comportement face à un statut non référencé."""
    allowed = planning_wf.get_allowed_transitions("STATUT_INEXISTANT")

    assert allowed == []
    assert "Aucune règle de transition trouvée" in caplog.text


# -----------------------------------------------------------------------------
# TESTS PARAMÉTRÉS (MATRICE DE TRANSITIONS)
# -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    "current, target, is_valid",
    [
        (PlanningStatusCode.BROUILLON, PlanningStatusCode.PUBLIE, True),
        (PlanningStatusCode.PUBLIE, PlanningStatusCode.TERMINE, True),
        (PlanningStatusCode.ANNULE, PlanningStatusCode.BROUILLON, True),
        (
            PlanningStatusCode.TERMINE,
            PlanningStatusCode.PUBLIE,
            False,
        ),  # Post-mortem interdit
        (
            PlanningStatusCode.PUBLIE,
            PlanningStatusCode.BROUILLON,
            False,
        ),  # Marche arrière interdite
    ],
)
def test_planning_matrix(planning_wf, current, target, is_valid):
    """Teste une matrice de transitions pour le planning."""
    if is_valid:
        planning_wf.validate_transition(current, target)
    else:
        with pytest.raises(AppException):
            planning_wf.validate_transition(current, target)

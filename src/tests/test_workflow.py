# src/tests/test_workflow.py
import pytest

from core.exceptions import BadRequestException
from mla_enum import AffectationStatusCode, PlanningStatusCode
from models import PlanningService
from services.assignement_service import AssignmentService
from services.planing_service import PlanningServiceSvc


def test_planning_workflow_success_publish(session, test_planning):
    """Scénario 1 : Transition valide Brouillon -> Publié"""
    svc = PlanningServiceSvc(session)

    # Assurer état initial
    test_planning.statut_code = PlanningStatusCode.BROUILLON.value
    session.flush()

    updated = svc.update_planning_status(test_planning.id, PlanningStatusCode.PUBLIE)
    assert updated.statut_code == PlanningStatusCode.PUBLIE.value


def test_planning_workflow_invalid_transition(session, test_planning):
    """Scénario 2 : Transition invalide Terminé -> Annulé"""
    svc = PlanningServiceSvc(session)

    test_planning.statut_code = PlanningStatusCode.TERMINE.value
    session.add(test_planning)
    session.commit()

    with pytest.raises(BadRequestException) as exc:
        svc.update_planning_status(test_planning.id, PlanningStatusCode.ANNULE)
    assert "Transition impossible" in str(exc.value)


def test_affectation_workflow_conditionnal(session, test_affectation, test_planning):
    """Scénario 3 : Transition affectation conditionnée par statut planning"""
    assign_svc = AssignmentService(session)

    # Planning est en brouillon par défaut dans les fixtures
    test_planning.statut_code = PlanningStatusCode.BROUILLON.value
    session.add(test_planning)
    session.flush()

    with pytest.raises(BadRequestException) as exc:
        assign_svc.update_affectation_status(
            test_affectation.id, AffectationStatusCode.PRESENT
        )
    assert "non publié" in str(exc.value)


def test_workflow_rollback_on_hook_failure(session, test_planning, monkeypatch):
    """Scénario 4 : Rollback si le hook échoue"""
    svc = PlanningServiceSvc(session)

    test_planning.statut_code = PlanningStatusCode.BROUILLON.value
    session.add(test_planning)
    session.commit()

    # Simuler une erreur dans le hook
    def mock_hook_fail(*args):
        raise RuntimeError("Erreur technique envoi email")

    monkeypatch.setattr(svc, "_on_publish_hook", mock_hook_fail)

    with pytest.raises(RuntimeError):
        svc.update_planning_status(test_planning.id, PlanningStatusCode.PUBLIE)

    # Vérifier que le statut n'a pas changé en base
    session.expire_all()
    db_planning = session.get(PlanningService, test_planning.id)
    assert db_planning.statut_code == PlanningStatusCode.BROUILLON.value

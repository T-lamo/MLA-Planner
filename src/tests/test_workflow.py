# src/tests/test_workflow.py
import pytest

from core.exceptions import BadRequestException
from mla_enum import AffectationStatusCode, PlanningStatusCode
from models import PlanningService
from models.schema_db_model import StatutPlanning
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

    # 1. S'assurer que le statut "TERMINE" existe en base (Seed)
    status_termine = session.get(StatutPlanning, PlanningStatusCode.TERMINE.value)
    if not status_termine:
        status_termine = StatutPlanning(
            code=PlanningStatusCode.TERMINE.value, libelle="Terminé"
        )
        session.add(status_termine)
        session.flush()  # Enregistre le statut sans commit

    # 2. Charger l'objet dans la session actuelle
    db_planning = session.get(PlanningService, test_planning.id)

    # 3. Mettre à jour le statut
    db_planning.statut_code = PlanningStatusCode.TERMINE.value

    # 4. Commit pour persister le statut 'TERMINE'
    session.commit()
    session.refresh(db_planning)  # Rafraîchir pour être sûr d'avoir l'état DB

    # 5. Tester la transition invalide
    with pytest.raises(BadRequestException) as exc:
        svc.update_planning_status(db_planning.id, PlanningStatusCode.ANNULE)

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

    planning_id = str(test_planning.id)
    test_planning.statut_code = PlanningStatusCode.BROUILLON.value
    session.add(test_planning)
    session.commit()

    # Simuler une erreur dans le hook
    def mock_hook_fail(*args):
        raise RuntimeError("Erreur technique envoi email")

    monkeypatch.setattr(svc, "_on_publish_hook", mock_hook_fail)

    with pytest.raises(RuntimeError):
        svc.update_planning_status(planning_id, PlanningStatusCode.PUBLIE)

    # Vérifier que le statut n'a pas changé en base
    session.expire_all()
    db_planning = session.get(PlanningService, planning_id)
    assert db_planning.statut_code == PlanningStatusCode.BROUILLON.value

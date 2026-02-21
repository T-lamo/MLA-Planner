import pytest

from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
from mla_enum import AffectationStatusCode, PlanningStatusCode
from models import PlanningService
from models.planning_model import PlanningFullUpdate
from models.schema_db_model import StatutPlanning
from services.affectation_service import AffectationService
from services.planing_service import PlanningServiceSvc

# On remplace l'ancienne BadRequestException par AppException dans les tests


def test_planning_workflow_success_publish(session, test_planning):
    svc = PlanningServiceSvc(session)
    test_planning.statut_code = PlanningStatusCode.BROUILLON.value
    session.flush()

    updated = svc.update_planning_status(test_planning.id, PlanningStatusCode.PUBLIE)
    assert updated.statut_code == PlanningStatusCode.PUBLIE.value


def test_planning_workflow_invalid_transition(session, test_planning):
    svc = PlanningServiceSvc(session)

    # Setup du statut
    status_termine = session.get(StatutPlanning, PlanningStatusCode.TERMINE.value)
    if not status_termine:
        status_termine = StatutPlanning(
            code=PlanningStatusCode.TERMINE.value, libelle="Terminé"
        )
        session.add(status_termine)
        session.flush()

    db_planning = session.get(PlanningService, test_planning.id)
    db_planning.statut_code = PlanningStatusCode.TERMINE.value
    session.commit()
    session.refresh(db_planning)

    with pytest.raises(AppException) as exc:
        svc.update_planning_status(db_planning.id, PlanningStatusCode.ANNULE)

    assert exc.value.code == ErrorRegistry.WORKFLOW_INVALID_TRANSITION.code
    # On peut maintenant tester le code d'erreur technique plutôt que juste le texte
    assert "Transition impossible" in str(exc.value)


def test_affectation_workflow_conditionnal(session, test_affectation, test_planning):
    assign_svc = AffectationService(session)
    test_planning.statut_code = PlanningStatusCode.BROUILLON.value
    session.add(test_planning)
    session.flush()

    # Changement : on catch AppException et on vérifie le code métier
    with pytest.raises(AppException) as exc:
        assign_svc.update_affectation_status(
            test_affectation.id, AffectationStatusCode.PRESENT
        )

    assert exc.value.code == ErrorRegistry.PLANNING_NOT_PUBLISHED.code


def test_workflow_rollback_on_hook_failure(session, test_planning, monkeypatch):
    svc = PlanningServiceSvc(session)
    planning_id = str(test_planning.id)
    test_planning.statut_code = PlanningStatusCode.BROUILLON.value
    session.add(test_planning)
    session.commit()

    def mock_hook_fail(*args):
        raise RuntimeError("Erreur technique envoi email")

    monkeypatch.setattr(svc, "_on_publish_hook", mock_hook_fail)

    with pytest.raises(RuntimeError):
        svc.update_planning_status(planning_id, PlanningStatusCode.PUBLIE)

    session.expire_all()
    db_planning = session.get(PlanningService, planning_id)
    assert db_planning.statut_code == PlanningStatusCode.BROUILLON.value


def test_sync_delete_slot(session, planning_svc, test_planning):
    payload = PlanningFullUpdate(slots=[])
    planning_svc.update_full_planning(test_planning.id, payload)
    session.refresh(test_planning)
    assert len(test_planning.slots) == 0


def test_immutability_failure(session, planning_svc, test_planning):
    test_planning.statut_code = PlanningStatusCode.TERMINE.value
    session.add(test_planning)
    session.flush()

    payload = PlanningFullUpdate(activite={"type": "Inchangeable"})

    # On vérifie à la fois le type d'exception et le code du registre
    with pytest.raises(AppException) as exc:
        planning_svc.update_full_planning(test_planning.id, payload)

    assert exc.value.code == ErrorRegistry.PLANNING_IMMUTABLE.code
    assert "modification interdite" in exc.value.message


def test_atomic_rollback_on_hook_failure(
    session, planning_svc, test_planning, monkeypatch
):
    original_type = test_planning.activite.type

    def mock_hook_fail(planning):
        raise RuntimeError("Hook Crash")

    monkeypatch.setattr(planning_svc, "_on_publish_hook", mock_hook_fail)

    payload = PlanningFullUpdate(
        activite={"type": "Nouveau Type"},
        planning={"statut_code": PlanningStatusCode.PUBLIE.value},
    )

    with pytest.raises(Exception, match="Hook Crash"):
        planning_svc.update_full_planning(test_planning.id, payload)

    session.refresh(test_planning)
    assert test_planning.activite.type == original_type
    assert test_planning.statut_code == PlanningStatusCode.BROUILLON.value


# pylint: disable=too-many-positional-arguments
def test_cross_workflow_violation(
    session, planning_svc, test_planning, test_slot, test_membre, test_membre_role
):
    test_planning.statut_code = PlanningStatusCode.BROUILLON.value
    session.add(test_planning)
    session.commit()

    affectation_payload = {
        "membre_id": str(test_membre.id),
        "role_code": test_membre_role.role_code,
        "statut_affectation_code": AffectationStatusCode.PRESENT.value,
    }

    slot_payload = {
        "id": str(test_slot.id),
        "nom_creneau": test_slot.nom_creneau,
        "date_debut": test_planning.activite.date_debut,
        "date_fin": test_planning.activite.date_fin,
        "affectations": [affectation_payload],
    }

    payload = PlanningFullUpdate(
        planning={"statut_code": PlanningStatusCode.BROUILLON.value},
        slots=[slot_payload],
    )

    with pytest.raises(AppException) as exc:
        planning_svc.update_full_planning(test_planning.id, payload)

    assert exc.value.code == ErrorRegistry.PLANNING_NOT_PUBLISHED.code


def test_valid_transition_triggers_hook(planning_svc, test_planning, monkeypatch):
    hook_called = False

    def mock_hook(_planning):
        nonlocal hook_called
        hook_called = True

    monkeypatch.setattr(planning_svc, "_on_publish_hook", mock_hook)

    payload = PlanningFullUpdate(
        planning={"statut_code": PlanningStatusCode.PUBLIE.value}
    )
    planning_svc.update_full_planning(test_planning.id, payload)

    assert hook_called is True

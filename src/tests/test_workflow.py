# src/tests/test_workflow.py
import pytest

from core.exceptions import BadRequestException
from mla_enum import AffectationStatusCode, PlanningStatusCode
from models import PlanningService
from models.planning_model import PlanningFullUpdate
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


def test_sync_delete_slot(session, planning_svc, test_planning):
    """Vérifie qu'un slot retiré du payload est supprimé de la DB."""
    # Correction : Utiliser explicitement le modèle
    payload = PlanningFullUpdate(slots=[])
    planning_svc.update_full_planning(test_planning.id, payload)

    session.refresh(test_planning)
    assert len(test_planning.slots) == 0


def test_immutability_failure(session, planning_svc, test_planning):
    """Vérifie le rejet de modification sur un planning TERMINE."""
    # On force le statut en base sans fermer la transaction
    test_planning.statut_code = PlanningStatusCode.TERMINE.value
    session.add(test_planning)
    session.flush()

    # Correction : Utiliser 'type' (champ réel) et non 'nom'
    # Utilisation d'un objet Pydantic propre
    payload = PlanningFullUpdate(activite={"type": "Inchangeable"})

    with pytest.raises(BadRequestException, match="modification interdite"):
        planning_svc.update_full_planning(test_planning.id, payload)


def test_atomic_rollback_on_hook_failure(
    session, planning_svc, test_planning, monkeypatch
):
    """Vérifie que l'activité n'est pas renommée si le hook échoue."""
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
    """Vérifie le blocage du pointage (PRESENT) sur un planning non publié."""
    test_planning.statut_code = PlanningStatusCode.BROUILLON.value
    session.add(test_planning)
    session.commit()

    # CORRECTION : Utilisation du bloc 'affectation' imbriqué pour le pointage
    affectation_payload = {
        "membre_id": str(test_membre.id),
        "role_code": test_membre_role.role_code,
        "planning": {"statut_code": PlanningStatusCode.PUBLIE.value},
        "statut_affectation_code": AffectationStatusCode.PRESENT.value,
    }

    activite = test_planning.activite
    slot_payload = {
        "id": str(test_slot.id),
        "nom_creneau": test_slot.nom_creneau,
        "date_debut": activite.date_debut,
        "date_fin": activite.date_fin,
        "affectations": [affectation_payload],
    }

    # CORRECTION : Utilisation du bloc 'planning' imbriqué
    payload = PlanningFullUpdate(
        planning={"statut_code": PlanningStatusCode.BROUILLON.value},
        slots=[slot_payload],
    )

    with pytest.raises(
        BadRequestException, match="Impossible de pointer sur un planning non publié."
    ) as exc:
        planning_svc.update_full_planning(test_planning.id, payload)

    assert "non publié" in str(exc.value)


def test_valid_transition_triggers_hook(planning_svc, test_planning, monkeypatch):
    """Vérifie que le passage à PUBLIE déclenche bien le hook."""
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

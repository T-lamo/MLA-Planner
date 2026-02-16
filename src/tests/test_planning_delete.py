import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
from mla_enum.custom_enum import PlanningStatusCode
from models import Activite, Affectation, PlanningService
from models.schema_db_model import Slot


class TestPlanningDeleteRobust:
    """Tests de suppression robuste pour le service Planning."""

    def test_delete_cascade_total_success(
        self, session, planning_svc, robust_data_factory
    ):
        """Vérifie le nettoyage complet
        (Activité -> Planning -> Slots -> Affectations)."""
        planning = robust_data_factory()
        p_id, a_id = planning.id, planning.activite_id
        s_ids = [s.id for s in planning.slots]

        planning_svc.delete_full_planning(p_id)
        session.flush()

        assert session.get(PlanningService, p_id) is None
        assert session.get(Activite, a_id) is None

        # Correction E1101: Utilisation de l'attribut de
        # classe explicite pour satisfaire Pylint
        stmt = select(Affectation).where(getattr(Affectation, "slot_id").in_(s_ids))
        remaining_affs = session.exec(stmt).all()
        assert len(remaining_affs) == 0

    def test_delete_atomic_rollback_on_deep_failure(
        self, session, planning_svc, robust_data_factory, monkeypatch
    ):
        """Vérifie l'atomicité via SAVEPOINT en cas d'erreur sur l'Activité."""
        planning = robust_data_factory()
        p_id, a_id = planning.id, planning.activite_id
        session.commit()

        original_delete = session.delete

        def mock_delete(obj):
            if isinstance(obj, Activite) and str(obj.id) == str(a_id):
                raise IntegrityError("Simulated Activity Failure", params={}, orig=None)
            return original_delete(obj)

        monkeypatch.setattr(session, "delete", mock_delete)

        with pytest.raises(IntegrityError):
            planning_svc.delete_full_planning(p_id)

        session.rollback()
        session.expire_all()

        db_p = session.exec(
            select(PlanningService).where(PlanningService.id == p_id)
        ).first()
        assert db_p is not None
        db_slots = session.exec(select(Slot).where(Slot.planning_id == p_id)).all()
        assert len(db_slots) > 0

    def test_delete_workflow_security_lock(self, planning_svc, robust_data_factory):
        """Vérifie le blocage de suppression si le planning est PUBLIE."""
        planning = robust_data_factory(status=PlanningStatusCode.PUBLIE.value)
        with pytest.raises(AppException) as exc:
            planning_svc.delete_full_planning(planning.id)

        assert exc.value.code == ErrorRegistry.PLANNING_DELETE_IMPOSSIBLE.code

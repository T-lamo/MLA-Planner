import pytest

from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
from services.affectation_service import AffectationService

# Importez vos fixtures de test et modèles ici


def test_assign_member_success(session, test_membre, test_slot, test_membre_role):
    # Setup : donner le rôle au membre
    # ... code pour lier test_membre et test_membre_role dans t_membre_role ...

    service = AffectationService(session)
    result = service.assign_member_to_slot(
        test_slot.id,
        test_membre.id,
        test_membre_role.role_code,
    )

    assert result.id is not None
    assert result.membre_id == test_membre.id
    assert result.statut_affectation_code == "PROPOSE"


def test_assign_member_missing_role(session, test_membre, test_slot):
    # Setup : membre n'a PAS le rôle

    service = AffectationService(session)

    with pytest.raises(AppException) as exc:
        service.assign_member_to_slot(test_slot.id, test_membre.id, "NON_EXISTANT_ROLE")

    assert exc.value.code == ErrorRegistry.ASGN_MEMBER_MISSING_ROLE.code

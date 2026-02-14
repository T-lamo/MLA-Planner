import pytest
from fastapi import HTTPException

from services.assignement_service import AssignmentService

# Importez vos fixtures de test et modèles ici


def test_assign_member_success(session, test_membre, test_slot, test_membre_role):
    # Setup : donner le rôle au membre
    # ... code pour lier test_membre et test_membre_role dans t_membre_role ...

    service = AssignmentService(session)
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

    service = AssignmentService(session)

    with pytest.raises(HTTPException) as excinfo:
        service.assign_member_to_slot(test_slot.id, test_membre.id, "NON_EXISTANT_ROLE")

    assert excinfo.value.status_code == 400
    assert "ne possède pas le rôle requis" in excinfo.value.detail

from models import MembreRole


def test_get_full_planning_complex_logic(
    session,
    planning_svc,
    test_membre,
    test_role_comp,
    valid_planning_full_payload,  # Injection de la fixture
):
    # 0. SETUP
    membre_role = MembreRole(membre_id=test_membre.id, role_code=test_role_comp.code)
    session.add(membre_role)
    session.flush()

    # 1. WHEN : Création et lecture
    # On utilise directement l'objet retourné par la fixture
    planning_db = planning_svc.create_full_planning(valid_planning_full_payload)
    session.flush()
    session.expire_all()

    full = planning_svc.get_full_planning(planning_db.id)

    # 2. THEN : Assertions
    assert full.id == planning_db.id
    assert len(full.slots) == 1
    assert full.slots[0].filling_rate == 50.0
    assert full.view_context.total_slots == 1

from fastapi import status
from models import MembreRole

# pylint: disable=unused-argument


# --- TESTS NOMINAUX ---
def test_assign_role_to_membre_success(
    client, admin_headers, test_membre, test_role_comp
):
    payload = {
        "membre_id": test_membre.id,
        "role_code": test_role_comp.code,
        "niveau": "EXPERT",
    }
    response = client.post(
        f"/membres/{test_membre.id}/roles", json=payload, headers=admin_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["role_code"] == "DEV_PYTHON"


def test_assign_role_non_existent_404(client, admin_headers, test_membre):
    payload = {
        "membre_id": test_membre.id,
        "role_code": "NOT_EXIST",
        "niveau": "DEBUTANT",
    }
    response = client.post(
        f"/membres/{test_membre.id}/roles", json=payload, headers=admin_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_membre_roles_list(
    client, admin_headers, test_membre, test_role_comp, session
):
    # Injection manuelle
    session.add(MembreRole(membre_id=test_membre.id, role_code=test_role_comp.code))
    session.flush()

    response = client.get(f"/membres/{test_membre.id}/roles", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


def test_remove_role_from_membre(
    client, admin_headers, test_membre, test_role_comp, session
):
    session.add(MembreRole(membre_id=test_membre.id, role_code=test_role_comp.code))
    session.flush()

    url = f"/membres/{test_membre.id}/roles/{test_role_comp.code}"
    response = client.delete(url, headers=admin_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT

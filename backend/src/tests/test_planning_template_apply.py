"""Tests US-02 : créer un planning depuis un template."""

# pylint: disable=redefined-outer-name

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from fastapi import status
from sqlmodel import Session

from models import Activite, Affectation, PlanningService, Slot
from models.planning_template_model import SaveAsTemplateRequest
from services.planning_template_service import PlanningTemplateSvc

# ---------------------------------------------------------------------------
# Helpers partagés
# ---------------------------------------------------------------------------

_BASE_CREATE = datetime(2026, 7, 1, 9, 0, 0)


def _build_payload(
    base: datetime,
    campus_id: str,
    ministere_id: str,
    *,
    template_id: str = "",
) -> dict:
    """Construit un payload POST /plannings/full."""
    payload: dict = {
        "activite": {
            "type": "Culte",
            "date_debut": base.isoformat(),
            "date_fin": (base + timedelta(hours=3)).isoformat(),
            "campus_id": campus_id,
            "ministere_organisateur_id": ministere_id,
        },
        "slots": [
            {
                "nom_creneau": "Louange",
                "date_debut": (base + timedelta(minutes=30)).isoformat(),
                "date_fin": (base + timedelta(hours=2)).isoformat(),
                "affectations": [],
            }
        ],
    }
    if template_id:
        payload["template_id"] = template_id
    return payload


# ---------------------------------------------------------------------------
# Fixtures locales
# ---------------------------------------------------------------------------


@pytest.fixture
def planning_for_template(session: Session, test_campus, test_ministere, test_membre):
    """Planning complet (activité + slot + affectation) pour créer un template."""
    base = _BASE_CREATE
    activite = Activite(
        type="Culte US02",
        date_debut=base,
        date_fin=base + timedelta(hours=3),
        campus_id=test_campus.id,
        ministere_organisateur_id=test_ministere.id,
    )
    session.add(activite)
    session.flush()

    planning = PlanningService(activite_id=activite.id, statut_code="BROUILLON")
    session.add(planning)
    session.flush()

    slot = Slot(
        planning_id=planning.id,
        nom_creneau="Louange",
        date_debut=base + timedelta(minutes=30),
        date_fin=base + timedelta(hours=2),
        nb_personnes_requis=2,
    )
    session.add(slot)
    session.flush()

    aff = Affectation(
        slot_id=slot.id,
        membre_id=test_membre.id,
        role_code="TENOR",
        statut_affectation_code="CONFIRME",
        presence_confirmee=False,
    )
    session.add(aff)
    session.flush()
    session.refresh(planning)
    return planning


@pytest.fixture
def existing_template(session: Session, planning_for_template, test_membre):
    """Template créé depuis planning_for_template."""
    svc = PlanningTemplateSvc(session)
    return svc.save_planning_as_template(
        planning_for_template.id,
        SaveAsTemplateRequest(nom="Template US02"),
        test_membre.id,
    )


# ---------------------------------------------------------------------------
# Tests API
# ---------------------------------------------------------------------------


def test_create_planning_with_template_id(
    client,
    admin_headers,
    session: Session,
    test_campus,
    test_ministere,
    *,
    test_membre,
    test_admin,
    existing_template,
):
    """POST /plannings/full avec template_id valide → 201, template_id stocké,
    used_count incrémenté d'1."""
    test_admin.membre_id = test_membre.id
    session.add(test_admin)
    session.commit()

    payload = _build_payload(
        datetime(2026, 8, 1, 9, 0, 0),
        test_campus.id,
        test_ministere.id,
        template_id=existing_template.id,
    )

    resp = client.post("/plannings/full", json=payload, headers=admin_headers)
    assert resp.status_code == status.HTTP_201_CREATED

    data = resp.json()["data"]
    assert data["template_id"] == existing_template.id

    # Vérifie que used_count a été incrémenté
    session.expire_all()
    updated = PlanningTemplateSvc(session).get_template(existing_template.id)
    assert updated.used_count == existing_template.used_count + 1


def test_create_planning_with_invalid_template_id(
    client,
    admin_headers,
    session: Session,
    test_campus,
    test_ministere,
    *,
    test_membre,
    test_admin,
):
    """POST /plannings/full avec template_id inexistant → 201 (défensif),
    template_id null dans la réponse."""
    test_admin.membre_id = test_membre.id
    session.add(test_admin)
    session.commit()

    payload = _build_payload(
        datetime(2026, 9, 1, 9, 0, 0),
        test_campus.id,
        test_ministere.id,
        template_id=str(uuid4()),
    )

    resp = client.post("/plannings/full", json=payload, headers=admin_headers)
    assert resp.status_code == status.HTTP_201_CREATED

    data = resp.json()["data"]
    assert data.get("template_id") is None

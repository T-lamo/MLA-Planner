"""Tests pour la fonctionnalité save-as-template (US-01)."""

# pylint: disable=redefined-outer-name

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from fastapi import status
from sqlmodel import Session

from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
from models import (
    Activite,
    Affectation,
    PlanningService,
    Slot,
)
from models.planning_template_model import (
    PlanningTemplateUpdate,
    SaveAsTemplateRequest,
)
from services.planning_template_service import PlanningTemplateSvc

# ---------------------------------------------------------------------------
# Fixtures locales
# ---------------------------------------------------------------------------


@pytest.fixture
def planning_with_slots(session: Session, test_campus, test_ministere, test_membre):
    """
    Crée un PlanningService complet (activité + 2 slots + affectations)
    utilisable pour les tests de création de template.
    """
    base = datetime(2026, 6, 1, 9, 0, 0)
    activite = Activite(
        type="Culte Test",
        date_debut=base,
        date_fin=base + timedelta(hours=12),
        campus_id=test_campus.id,
        ministere_organisateur_id=test_ministere.id,
    )
    session.add(activite)
    session.flush()

    planning = PlanningService(
        activite_id=activite.id,
        statut_code="BROUILLON",
    )
    session.add(planning)
    session.flush()

    slot_a = Slot(
        planning_id=planning.id,
        nom_creneau="Louange Matin",
        date_debut=base + timedelta(hours=1),
        date_fin=base + timedelta(hours=3),
        nb_personnes_requis=2,
    )
    slot_b = Slot(
        planning_id=planning.id,
        nom_creneau="Accueil",
        date_debut=base + timedelta(hours=4),
        date_fin=base + timedelta(hours=6),
        nb_personnes_requis=3,
    )
    session.add_all([slot_a, slot_b])
    session.flush()

    aff1 = Affectation(
        slot_id=slot_a.id,
        membre_id=test_membre.id,
        role_code="TENOR",
        statut_affectation_code="CONFIRME",
        presence_confirmee=False,
    )
    # Même role_code → doit être dédupliqué dans le template
    aff2 = Affectation(
        slot_id=slot_a.id,
        membre_id=test_membre.id,
        role_code="TENOR",
        statut_affectation_code="CONFIRME",
        presence_confirmee=False,
    )
    aff3 = Affectation(
        slot_id=slot_b.id,
        membre_id=test_membre.id,
        role_code="HOTE_ACCUEIL",
        statut_affectation_code="CONFIRME",
        presence_confirmee=False,
    )
    session.add_all([aff1, aff2, aff3])
    session.flush()
    session.refresh(planning)
    return planning


@pytest.fixture
def created_by_id(test_membre):
    """ID du créateur (membre existant en DB requis par la FK)."""
    return test_membre.id


# ---------------------------------------------------------------------------
# Tests service (couche métier)
# ---------------------------------------------------------------------------


def test_save_as_template_happy_path(session, planning_with_slots, created_by_id):
    """Un planning valide → template créé avec le bon nombre de créneaux."""
    svc = PlanningTemplateSvc(session)
    result = svc.save_planning_as_template(
        planning_with_slots.id,
        type(
            "Req",
            (),
            {"nom": "Mon Template", "description": "Desc test"},
        )(),
        created_by_id,
    )
    assert result.nom == "Mon Template"
    assert len(result.slots) == 2
    slot_noms = {s.nom_creneau for s in result.slots}
    assert "Louange Matin" in slot_noms
    assert "Accueil" in slot_noms


def test_save_as_template_deduplicates_roles(
    session, planning_with_slots, created_by_id
):
    """2 affectations avec le même role_code → 1 PlanningTemplateRole."""
    svc = PlanningTemplateSvc(session)
    result = svc.save_planning_as_template(
        planning_with_slots.id,
        SaveAsTemplateRequest(nom="Dedup Test"),
        created_by_id,
    )
    # slot_a a 2 affectations TENOR → doit être dédupliqué en 1 rôle
    slot_a = next(s for s in result.slots if s.nom_creneau == "Louange Matin")
    assert len(slot_a.roles) == 1
    assert slot_a.roles[0].role_code == "TENOR"


def test_save_as_template_excludes_membres(session, planning_with_slots, created_by_id):
    """Les IDs de membres ne sont PAS stockés dans le template."""
    svc = PlanningTemplateSvc(session)
    result = svc.save_planning_as_template(
        planning_with_slots.id,
        SaveAsTemplateRequest(nom="No Membres"),
        created_by_id,
    )
    # PlanningTemplateRole ne contient que role_code, pas de membre_id
    for slot in result.slots:
        for role in slot.roles:
            assert hasattr(role, "role_code")
            assert not hasattr(role, "membre_id")


def test_save_as_template_planning_not_found(session, created_by_id):
    """ID inconnu → AppException PLAN_014."""
    svc = PlanningTemplateSvc(session)
    with pytest.raises(AppException) as exc:
        svc.save_planning_as_template(
            str(uuid4()),
            SaveAsTemplateRequest(nom="Ghost"),
            created_by_id,
        )
    assert exc.value.code == ErrorRegistry.PLAN_014.code


def test_get_template_not_found(session):
    """ID template inconnu → AppException PLAN_013."""
    svc = PlanningTemplateSvc(session)
    with pytest.raises(AppException) as exc:
        svc.get_template(str(uuid4()))
    assert exc.value.code == ErrorRegistry.PLAN_013.code


def test_delete_template_cascades(session, planning_with_slots, created_by_id):
    """Suppression du template → GET retourne PLAN_013."""
    svc = PlanningTemplateSvc(session)
    result = svc.save_planning_as_template(
        planning_with_slots.id,
        SaveAsTemplateRequest(nom="À supprimer"),
        created_by_id,
    )
    template_id = result.id
    svc.delete_template(template_id)
    with pytest.raises(AppException) as exc:
        svc.get_template(template_id)
    assert exc.value.code == ErrorRegistry.PLAN_013.code


def test_list_by_campus_returns_templates(
    session, planning_with_slots, created_by_id, test_campus
):
    """Template créé → apparaît dans list_by_campus du bon campus."""
    svc = PlanningTemplateSvc(session)
    svc.save_planning_as_template(
        planning_with_slots.id,
        SaveAsTemplateRequest(nom="Campus Template"),
        created_by_id,
    )
    results = svc.list_by_campus(test_campus.id)
    noms = [r.nom for r in results]
    assert "Campus Template" in noms


def test_update_template_nom(session, planning_with_slots, created_by_id):
    """PATCH nom → GET retourne le nouveau nom."""
    svc = PlanningTemplateSvc(session)
    created = svc.save_planning_as_template(
        planning_with_slots.id,
        SaveAsTemplateRequest(nom="Ancien Nom"),
        created_by_id,
    )
    updated = svc.update_template(created.id, PlanningTemplateUpdate(nom="Nouveau Nom"))
    assert updated.nom == "Nouveau Nom"
    fetched = svc.get_template(created.id)
    assert fetched.nom == "Nouveau Nom"


# ---------------------------------------------------------------------------
# Tests API (couche HTTP)
# ---------------------------------------------------------------------------


def test_save_as_template_requires_write_role(
    client, user_headers, planning_with_slots
):
    """Utilisateur standard (MEMBRE_MLA) → 403 Forbidden."""
    resp = client.post(
        f"/planning-templates/from-planning/{planning_with_slots.id}",
        json={"nom": "Interdit"},
        headers=user_headers,
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_api_save_as_template_happy_path(
    client,
    admin_headers,
    session,
    planning_with_slots,
    *,
    test_admin,
    test_membre,
):
    """Admin → 201, template bien créé."""
    # Lie l'admin à un membre existant pour satisfaire la FK created_by_id
    test_admin.membre_id = test_membre.id
    session.add(test_admin)
    session.commit()
    resp = client.post(
        f"/planning-templates/from-planning/{planning_with_slots.id}",
        json={"nom": "API Template", "description": "Via API"},
        headers=admin_headers,
    )
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()["data"]
    assert data["nom"] == "API Template"
    assert len(data["slots"]) == 2


def test_api_get_template_not_found(client, admin_headers):
    """GET template inconnu → 404."""
    resp = client.get(
        f"/planning-templates/{uuid4()}",
        headers=admin_headers,
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert resp.json()["error"]["code"] == ErrorRegistry.PLAN_013.code

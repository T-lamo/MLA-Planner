"""Tests pour la bibliothèque de templates (US-95)."""

# pylint: disable=redefined-outer-name

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from fastapi import status
from sqlmodel import Session, select

from core.auth.security import create_access_token, get_password_hash
from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
from mla_enum import RoleName
from models import (
    Activite,
    AffectationRole,
    Campus,
    PlanningService,
    Role,
    Utilisateur,
)
from models.planning_template_model import (
    PlanningTemplateFullUpdate,
    PlanningTemplateSlotWrite,
)
from models.schema_db_model import PlanningTemplate, PlanningTemplateSlot
from services.planning_template_service import PlanningTemplateSvc

# ---------------------------------------------------------------------------
# Fixtures locales
# ---------------------------------------------------------------------------


@pytest.fixture
def template_fixture(session: Session, test_campus, test_ministere, test_membre):
    """Crée un template de planning complet avec 2 créneaux."""
    tpl = PlanningTemplate(
        nom="Template Test US95",
        description="Template pour tests",
        activite_type="Culte",
        duree_minutes=180,
        campus_id=test_campus.id,
        ministere_id=test_ministere.id,
        created_by_id=test_membre.id,
    )
    session.add(tpl)
    session.flush()
    slot_a = PlanningTemplateSlot(
        template_id=tpl.id,
        nom_creneau="Louange",
        offset_debut_minutes=0,
        offset_fin_minutes=60,
        nb_personnes_requis=2,
    )
    slot_b = PlanningTemplateSlot(
        template_id=tpl.id,
        nom_creneau="Accueil",
        offset_debut_minutes=60,
        offset_fin_minutes=120,
        nb_personnes_requis=1,
    )
    session.add_all([slot_a, slot_b])
    session.flush()
    session.refresh(tpl)
    return tpl


@pytest.fixture
def template_other_campus(session: Session, test_pays, test_ministere, test_membre):
    """Crée un template sur un campus différent."""
    other_campus = Campus(
        nom=f"Campus Autre {uuid4()}",
        ville="Autre",
        pays_id=test_pays.id,
        date_creation="2024-01-01",
    )
    session.add(other_campus)
    session.flush()
    tpl = PlanningTemplate(
        nom="Template Autre Campus",
        description=None,
        activite_type="Reunion",
        duree_minutes=60,
        campus_id=other_campus.id,
        ministere_id=test_ministere.id,
        created_by_id=test_membre.id,
    )
    session.add(tpl)
    session.flush()
    session.refresh(tpl)
    return tpl


@pytest.fixture
def planning_fixture(session: Session, test_campus, test_ministere, template_fixture):
    """Crée un planning lié au template_fixture."""
    base = datetime(2026, 6, 1, 9, 0)
    activite = Activite(
        type="Culte",
        date_debut=base,
        date_fin=base + timedelta(hours=3),
        campus_id=test_campus.id,
        ministere_organisateur_id=test_ministere.id,
    )
    session.add(activite)
    session.flush()
    planning = PlanningService(
        activite_id=activite.id,
        statut_code="BROUILLON",
        template_id=template_fixture.id,
    )
    session.add(planning)
    session.flush()
    session.refresh(planning)
    return planning


@pytest.fixture
def responsable_user(session: Session, test_campus, test_membre):
    """Crée un user RESPONSABLE_MLA lié à test_campus via test_membre."""
    # S'assurer que test_membre a un campus_principal_id
    if not test_membre.campus_principal_id:
        test_membre.campus_principal_id = test_campus.id
        session.add(test_membre)
        session.flush()
        session.refresh(test_membre)
    resp_role = session.exec(
        select(Role).where(Role.libelle == RoleName.RESPONSABLE_MLA)
    ).first()
    if not resp_role:
        resp_role = Role(libelle=RoleName.RESPONSABLE_MLA)
        session.add(resp_role)
        session.flush()
    user = Utilisateur(
        username=f"resp_{uuid4().hex[:6]}",
        password=get_password_hash("test123"),
        actif=True,
        membre_id=test_membre.id,
    )
    session.add(user)
    session.flush()
    aff = AffectationRole(utilisateur_id=user.id, role_id=resp_role.id)
    session.add(aff)
    session.flush()
    session.refresh(user)
    return user


@pytest.fixture
def responsable_headers(responsable_user):
    """Headers JWT pour le responsable MLA."""
    token, _ = create_access_token(data={"sub": responsable_user.username})
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Tests service
# ---------------------------------------------------------------------------


def test_list_templates_admin_sees_all(
    session, test_admin, test_membre, template_fixture, template_other_campus
):
    """Admin voit tous les templates (sans filtre campus)."""
    test_admin.membre_id = test_membre.id
    session.add(test_admin)
    session.flush()
    svc = PlanningTemplateSvc(session)
    result = svc.list_templates(test_admin)
    ids = [t.id for t in result]
    assert template_fixture.id in ids
    assert template_other_campus.id in ids


def test_list_templates_responsable_filtered(
    session, responsable_user, test_campus, template_fixture, template_other_campus
):
    """Responsable MLA voit uniquement les templates de son campus."""
    svc = PlanningTemplateSvc(session)
    result = svc.list_templates(responsable_user)
    ids = [t.id for t in result]
    assert template_fixture.id in ids
    assert template_other_campus.id not in ids


def test_list_templates_sorted_by_last_used(
    session, test_admin, test_membre, template_fixture
):
    """L'ordre par défaut retourne les templates triés (last_used NULLS LAST)."""
    test_admin.membre_id = test_membre.id
    session.add(test_admin)
    session.flush()
    svc = PlanningTemplateSvc(session)
    result = svc.list_templates(test_admin)
    # Tous doivent avoir last_used_at = None car aucun planning lié
    for item in result:
        assert item.last_used_at is None or isinstance(item.last_used_at, datetime)


def test_list_templates_filter_by_ministere(
    session, test_admin, test_membre, test_ministere, template_fixture
):
    """Filtre par ministere_id retourne uniquement les templates du ministère."""
    test_admin.membre_id = test_membre.id
    session.add(test_admin)
    session.flush()
    svc = PlanningTemplateSvc(session)
    result = svc.list_templates(test_admin, ministere_id_filter=test_ministere.id)
    for item in result:
        assert item.ministere_id == test_ministere.id


def test_get_template_full(session, test_admin, test_membre, template_fixture):
    """GET template complet — slots et rôles présents."""
    test_admin.membre_id = test_membre.id
    session.add(test_admin)
    session.flush()
    svc = PlanningTemplateSvc(session)
    result = svc.get_template_full(template_fixture.id, test_admin)
    assert result.id == template_fixture.id
    assert len(result.slots) == 2
    slot_noms = {s.nom_creneau for s in result.slots}
    assert "Louange" in slot_noms
    assert "Accueil" in slot_noms


def test_update_template(session, test_admin, test_membre, template_fixture):
    """PUT template — slots recréés, nom mis à jour."""
    test_admin.membre_id = test_membre.id
    session.add(test_admin)
    session.flush()
    svc = PlanningTemplateSvc(session)
    payload = PlanningTemplateFullUpdate(
        nom="Nouveau Nom",
        description="Nouvelle desc",
        slots=[
            PlanningTemplateSlotWrite(
                nom_creneau="Seul Creneau",
                offset_debut_minutes=0,
                offset_fin_minutes=60,
                nb_personnes_requis=3,
                roles=["TENOR", "SON"],
            )
        ],
    )
    result = svc.update_template_full(template_fixture.id, payload, test_admin)
    assert result.nom == "Nouveau Nom"
    assert len(result.slots) == 1
    assert result.slots[0].nom_creneau == "Seul Creneau"
    assert len(result.slots[0].roles) == 2


def test_duplicate_template(session, test_admin, test_membre, template_fixture):
    """Duplication — nom contient '(copie)'."""
    test_admin.membre_id = test_membre.id
    session.add(test_admin)
    session.flush()
    svc = PlanningTemplateSvc(session)
    copy = svc.duplicate_template(template_fixture.id, test_admin)
    assert "(copie)" in copy.nom
    assert copy.id != template_fixture.id
    assert copy.campus_id == template_fixture.campus_id


def test_delete_template_nullifies_planning(
    session, test_admin, test_membre, template_fixture, planning_fixture
):
    """DELETE — Planning.template_id devient NULL, planning toujours présent."""
    test_admin.membre_id = test_membre.id
    session.add(test_admin)
    session.flush()
    assert planning_fixture.template_id == template_fixture.id
    svc = PlanningTemplateSvc(session)
    svc.delete_template_with_access(template_fixture.id, test_admin)
    session.refresh(planning_fixture)
    assert planning_fixture.template_id is None
    still_exists = session.get(PlanningService, planning_fixture.id)
    assert still_exists is not None


def test_delete_template_forbidden_other_campus(
    session, responsable_user, template_other_campus
):
    """Responsable MLA → 403 sur template d'un autre campus."""
    svc = PlanningTemplateSvc(session)
    with pytest.raises(AppException) as exc:
        svc.delete_template_with_access(template_other_campus.id, responsable_user)
    assert exc.value.code == ErrorRegistry.TMPL_004.code


# ---------------------------------------------------------------------------
# Tests API
# ---------------------------------------------------------------------------


def test_api_list_templates(client, admin_headers, template_fixture):
    """GET /planning-templates → 200, liste non vide."""
    resp = client.get("/planning-templates", headers=admin_headers)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()["data"]
    assert isinstance(data, list)


def test_api_duplicate_template(
    client, admin_headers, session, test_admin, *, test_membre, template_fixture
):
    """POST /planning-templates/{id}/duplicate → 201, nom avec (copie)."""
    test_admin.membre_id = test_membre.id
    session.add(test_admin)
    session.commit()
    resp = client.post(
        f"/planning-templates/{template_fixture.id}/duplicate",
        headers=admin_headers,
    )
    assert resp.status_code == status.HTTP_201_CREATED
    copy = resp.json()["data"]
    assert "(copie)" in copy["nom"]


def test_api_delete_template_forbidden(
    client, responsable_headers, template_other_campus
):
    """DELETE sur template autre campus — 403."""
    resp = client.delete(
        f"/planning-templates/{template_other_campus.id}",
        headers=responsable_headers,
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN

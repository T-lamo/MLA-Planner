from datetime import datetime, timedelta
from typing import List
from uuid import uuid4

import pytest
from core.workflow_engine import (
    WorkflowEngine,
    affectation_transitions,
    planning_transitions,
)
from mla_enum import AffectationStatusCode
from mla_enum.custom_enum import PlanningStatusCode
from models import (
    Activite,
    ActiviteCreate,
    Affectation,
    AffectationSimpleCreate,
    CategorieRole,
    Membre,
    MembreRole,
    PlanningFullCreate,
    PlanningService,
    PlanningServiceCreate,
    RoleCompetence,
    Slot,
    SlotFullNested,
    StatutAffectation,
    StatutPlanning,
)
from services.planing_service import PlanningServiceSvc
from sqlmodel import Session


# pylint: disable=redefined-outer-name
@pytest.fixture
def test_cat(session):
    """Crée une catégorie de base pour les rôles."""
    cat = CategorieRole(code="TECH", libelle="Technique")
    session.add(cat)
    session.flush()
    return cat


@pytest.fixture
def test_role_comp(session: Session, test_cat: CategorieRole) -> RoleCompetence:
    """Fixture pour créer un rôle de compétence lié à la catégorie de test."""
    role = RoleCompetence(
        code="DEV_PYTHON", libelle="Développeur Python", categorie_code=test_cat.code
    )
    session.add(role)
    session.flush()
    session.refresh(role)
    return role


@pytest.fixture
def test_activite(session: Session, test_campus, test_ministere) -> Activite:
    """
    Fixture pour créer une activité valide.
    Répond aux contraintes du nouveau schéma (type, ministere_organisateur, dates).
    """
    activite = Activite(
        nom=f"Activite Test {uuid4().hex[:6]}",
        type="Réunion",  # Valeur requise par la contrainte NOT NULL
        campus_id=test_campus.id,
        ministere_organisateur_id=test_ministere.id,
        date_debut=datetime.now(),
        date_fin=datetime.now() + timedelta(hours=2),
    )

    session.add(activite)
    session.flush()
    session.refresh(activite)
    return activite


@pytest.fixture
def activite_data(test_campus, test_ministere):
    return {
        "type": "Culte",
        "date_debut": (datetime.now() + timedelta(days=1)).isoformat(),
        "date_fin": (datetime.now() + timedelta(days=1, hours=2)).isoformat(),
        "lieu": "Auditorium Principal",
        "description": "Culte dominical",
        "campus_id": test_campus.id,
        "ministere_organisateur_id": test_ministere.id,
    }


@pytest.fixture(autouse=True)
def seed_planning_status(session: Session):
    """Populate the reference table for statuses before each test."""
    codes = [
        "BROUILLON",
        "PUBLIE",
        "ANNULE",
        "TERMINE",
    ]
    for code in codes:
        # We use merge to avoid conflicts if the status already exists
        session.merge(StatutPlanning(code=code, libelle=code.capitalize()))
    session.flush()


@pytest.fixture
def test_slot(session, test_planning):
    """Fixture pour créer un Slot (créneau) valide."""
    # On définit des dates cohérentes avec l'activité parente si possible
    maintenant = datetime.now()
    slot = Slot(
        id=str(uuid4()),
        planning_id=test_planning.id,
        nom_creneau="Session de Louange",
        date_debut=maintenant + timedelta(hours=1),
        date_fin=maintenant + timedelta(hours=2),
    )
    session.add(slot)
    session.flush()
    session.refresh(slot)
    return slot


@pytest.fixture
def test_statut_brouillon(session):
    """
    Assure que le statut BROUILLON existe dans la table de référence.
    C'est crucial car statut_code est une foreign_key.
    """

    statut = session.get(StatutPlanning, "BROUILLON")
    if not statut:
        statut = StatutPlanning(code="BROUILLON")  # libelle="Brouillon"
        session.add(statut)
        session.flush()
        session.refresh(statut)
    return statut


@pytest.fixture
def test_planning(session, test_activite):
    """Fixture simplifiée utilisant les codes de l'Enum."""
    planning = PlanningService(
        activite_id=test_activite.id,
        statut_code=PlanningStatusCode.BROUILLON.value,
    )
    session.add(planning)
    session.flush()
    session.refresh(planning)
    return planning


@pytest.fixture
def test_membre_role(session, test_membre, test_role_comp):
    """
    Crée le lien MembreRole (MembreRole).
    """
    membre_role = MembreRole(
        membre_id=test_membre.id,
        role_code=test_role_comp.code,
        niveau="INTERMEDIAIRE",
        is_principal=True,
    )
    session.add(membre_role)
    session.flush()
    session.refresh(membre_role)
    return membre_role


@pytest.fixture(autouse=True)
def seed_affectation_status(session: Session):
    """Popule la table de référence des statuts d'affectation."""

    for status in AffectationStatusCode:
        session.merge(
            StatutAffectation(code=status.value, libelle=status.value.capitalize())
        )
    session.flush()


@pytest.fixture
def test_affectation(session, test_slot, test_membre) -> Affectation:
    """Fixture pour créer une affectation valide liée à un slot et un membre."""

    # On s'assure que le statut existe
    # (déjà fait par seed_affectation_status en autouse)
    affectation = Affectation(
        slot_id=test_slot.id,
        membre_id=test_membre.id,
        role_code="ROLE_TEST",
        # Par défaut dans le workflow, une affectation est PROPOSE
        statut_affectation_code=AffectationStatusCode.PROPOSE.value,
        presence_confirmee=False,
    )

    session.add(affectation)
    # Important : flush() au lieu de flush() pour ne pas fermer
    # la transaction de la session de test
    session.flush()
    session.refresh(affectation)
    return affectation


@pytest.fixture
def planning_svc(session):
    """Injecte le service avec la session de transaction de test."""
    return PlanningServiceSvc(session)


def _create_robust_members(session, campus_id, role_code) -> List[Membre]:
    """Crée des membres avec les rôles nécessaires pour les tests."""
    membres = []
    for i in range(3):
        m = Membre(
            nom=f"NOM_{uuid4().hex[:4]}",
            prenom=f"PRENOM_{i}",
            email=f"robust_{i}_{uuid4().hex[:4]}@test.com",
            campus_id=campus_id,
            actif=True,
        )
        session.add(m)
        session.flush()
        m_role = MembreRole(
            membre_id=m.id,
            role_code=role_code,
            niveau="EXPERT",
            is_principal=True,
        )
        session.add(m_role)
        membres.append(m)
    return membres


def _prepare_slots_payload(base_dt, membres, role_code) -> List[SlotFullNested]:
    """Prépare les payloads de slots sans collision."""
    slots = []
    for s_idx in range(2):
        start = base_dt + timedelta(hours=1 + (s_idx * 2))
        end = start + timedelta(hours=2)
        affs = [
            AffectationSimpleCreate(membre_id=str(m.id), role_code=role_code)
            for m in membres
        ]
        slots.append(
            SlotFullNested(
                nom_creneau=f"Slot {s_idx}",
                date_debut=start,
                date_fin=end,
                affectations=affs,
            )
        )
    return slots


@pytest.fixture
def robust_data_factory(session, test_campus, test_ministere, test_role_comp):
    """
    Générateur global de planning complexe.
    """

    def _create_complex_tree(status: str = "BROUILLON"):
        base_date = datetime(2026, 6, 1, 8, 0, 0)
        membres = _create_robust_members(session, test_campus.id, test_role_comp.code)
        session.flush()

        full_data = PlanningFullCreate(
            activite=ActiviteCreate(
                nom=f"Event_{uuid4().hex[:4]}",
                type="Culte",
                campus_id=str(test_campus.id),
                ministere_organisateur_id=str(test_ministere.id),
                date_debut=base_date,
                date_fin=base_date + timedelta(hours=15),
            ),
            planning=PlanningServiceCreate(
                statut_code=status, activite_id=str(uuid4())
            ),
            slots=_prepare_slots_payload(base_date, membres, test_role_comp.code),
        )

        return PlanningServiceSvc(session).create_full_planning(full_data)

    return _create_complex_tree


@pytest.fixture
def planning_wf():
    """Fixture instanciant le moteur pour les plannings."""
    return WorkflowEngine(planning_transitions)


@pytest.fixture
def affectation_wf():
    """Fixture instanciant le moteur pour les affectations."""
    return WorkflowEngine(affectation_transitions)


@pytest.fixture
def valid_planning_full_payload(
    test_campus, test_ministere, test_membre, test_role_comp
):
    """
    Génère un payload PlanningFullCreate valide et réutilisable.
    """
    base_date = datetime(2026, 2, 16, 9, 0, 0)

    return PlanningFullCreate(
        activite=ActiviteCreate(
            type="Culte",
            campus_id=str(test_campus.id),
            ministere_organisateur_id=str(test_ministere.id),
            date_debut=base_date,
            date_fin=base_date + timedelta(hours=3),
            lieu="Main Hall",
        ),
        planning=PlanningServiceCreate(
            statut_code=PlanningStatusCode.BROUILLON.value,
            activite_id=None,
        ),
        slots=[
            SlotFullNested(
                nom_creneau="Louange",
                date_debut=base_date + timedelta(minutes=30),
                date_fin=base_date + timedelta(hours=1),
                nb_personnes_requis=2,
                affectations=[
                    AffectationSimpleCreate(
                        membre_id=str(test_membre.id),
                        role_code=test_role_comp.code,
                        statut_assignation_code="CONFIRME",
                    )
                ],
            )
        ],
    )

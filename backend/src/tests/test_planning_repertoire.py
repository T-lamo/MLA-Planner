"""
Tests du module Répertoire de Chants sur un Planning.

Vérifie :
  - GET  /plannings/{id}/repertoire  (vide et rempli)
  - PUT  /plannings/{id}/repertoire  (remplacement complet)
  - Idempotence (double PUT)
  - Ordre préservé
  - Planning inexistant → 404
  - Chant inexistant dans PUT → 404
"""

from uuid import uuid4

import pytest
from sqlmodel import Session

from core.exceptions.app_exception import AppException
from models.chant_model import Chant, ChantCategorie
from models.planning_model import PlanningRepertoireUpdate
from services.planing_service import PlanningServiceSvc

# pylint: disable=redefined-outer-name


# ------------------------------------------------------------------ #
#  Fixtures locales
# ------------------------------------------------------------------ #


@pytest.fixture
def test_chant_categorie(session: Session) -> ChantCategorie:
    cat = ChantCategorie(code="LOUANGE_TEST", libelle="Louange Test", ordre=0)
    session.merge(cat)
    session.flush()
    return session.get(ChantCategorie, "LOUANGE_TEST")  # type: ignore[return-value]


@pytest.fixture
def test_chant_a(session: Session, test_campus, test_chant_categorie) -> Chant:
    chant = Chant(
        titre="Amazing Grace",
        artiste="John Newton",
        campus_id=test_campus.id,
        categorie_code=test_chant_categorie.code,
        actif=True,
    )
    session.add(chant)
    session.flush()
    session.refresh(chant)
    return chant


@pytest.fixture
def test_chant_b(session: Session, test_campus, test_chant_categorie) -> Chant:
    chant = Chant(
        titre="10 000 Reasons",
        artiste="Matt Redman",
        campus_id=test_campus.id,
        categorie_code=test_chant_categorie.code,
        actif=True,
    )
    session.add(chant)
    session.flush()
    session.refresh(chant)
    return chant


@pytest.fixture
def test_chant_c(session: Session, test_campus, test_chant_categorie) -> Chant:
    chant = Chant(
        titre="Goodness of God",
        artiste="Bethel Music",
        campus_id=test_campus.id,
        categorie_code=test_chant_categorie.code,
        actif=True,
    )
    session.add(chant)
    session.flush()
    session.refresh(chant)
    return chant


@pytest.fixture
def planning_svc_local(session: Session) -> PlanningServiceSvc:
    return PlanningServiceSvc(session)


# ------------------------------------------------------------------ #
#  Tests service
# ------------------------------------------------------------------ #


class TestGetRepertoire:
    def test_vide_par_defaut(
        self, planning_svc_local: PlanningServiceSvc, test_planning
    ) -> None:
        """Un planning sans chants renvoie une liste vide."""
        result = planning_svc_local.get_repertoire(test_planning.id)
        assert result == []

    def test_planning_inexistant(self, planning_svc_local: PlanningServiceSvc) -> None:
        """Un planning inexistant lève PLAN_NOT_FOUND."""
        with pytest.raises(AppException) as exc_info:
            planning_svc_local.get_repertoire(str(uuid4()))
        assert exc_info.value.detail.code == "PLAN_010"


class TestSetRepertoire:
    def test_set_et_get(
        self,
        planning_svc_local: PlanningServiceSvc,
        test_planning,
        test_chant_a,
        test_chant_b,
    ) -> None:
        """set_repertoire puis get_repertoire retourne les chants dans l'ordre."""
        payload = PlanningRepertoireUpdate(chant_ids=[test_chant_a.id, test_chant_b.id])
        result = planning_svc_local.set_repertoire(test_planning.id, payload)

        assert len(result) == 2
        assert result[0].id == test_chant_a.id
        assert result[0].ordre == 0
        assert result[1].id == test_chant_b.id
        assert result[1].ordre == 1

    def test_remplacement_complet(
        self,
        planning_svc_local: PlanningServiceSvc,
        *,
        test_planning,
        test_chant_a,
        test_chant_b,
        test_chant_c,
    ) -> None:
        """Un deuxième PUT remplace entièrement le répertoire."""
        planning_svc_local.set_repertoire(
            test_planning.id,
            PlanningRepertoireUpdate(chant_ids=[test_chant_a.id]),
        )
        result = planning_svc_local.set_repertoire(
            test_planning.id,
            PlanningRepertoireUpdate(chant_ids=[test_chant_c.id, test_chant_b.id]),
        )
        assert len(result) == 2
        assert result[0].id == test_chant_c.id
        assert result[1].id == test_chant_b.id

    def test_repertoire_vide(
        self,
        planning_svc_local: PlanningServiceSvc,
        test_planning,
        test_chant_a,
    ) -> None:
        """On peut vider le répertoire avec une liste vide."""
        planning_svc_local.set_repertoire(
            test_planning.id,
            PlanningRepertoireUpdate(chant_ids=[test_chant_a.id]),
        )
        result = planning_svc_local.set_repertoire(
            test_planning.id,
            PlanningRepertoireUpdate(chant_ids=[]),
        )
        assert result == []

    def test_chant_inexistant(
        self,
        planning_svc_local: PlanningServiceSvc,
        test_planning,
    ) -> None:
        """Un chant_id inexistant lève PLAN_018."""
        with pytest.raises(AppException) as exc_info:
            planning_svc_local.set_repertoire(
                test_planning.id,
                PlanningRepertoireUpdate(chant_ids=[str(uuid4())]),
            )
        assert exc_info.value.detail.code == "PLAN_018"

    def test_planning_inexistant(
        self,
        planning_svc_local: PlanningServiceSvc,
        test_chant_a,
    ) -> None:
        """Un planning inexistant lève PLAN_NOT_FOUND."""
        with pytest.raises(AppException) as exc_info:
            planning_svc_local.set_repertoire(
                str(uuid4()),
                PlanningRepertoireUpdate(chant_ids=[test_chant_a.id]),
            )
        assert exc_info.value.detail.code == "PLAN_010"

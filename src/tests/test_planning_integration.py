from datetime import datetime, timedelta

from fastapi import status
from sqlmodel import select

from models import Activite, PlanningService
from models.activite_model import ActiviteCreate, ActiviteUpdate
from models.planning_model import (
    AssignmentSimpleCreate,
    PlanningFullCreate,
    PlanningFullUpdate,
    PlanningServiceCreate,
    SlotFullNested,
    SlotFullUpdate,
)
from models.schema_db_model import MembreRole


# pylint: disable=too-many-positional-arguments
def test_api_create_full_planning_success(
    client,
    admin_headers,
    session,
    test_campus,
    test_ministere,
    test_membre,
    test_role_comp,
):
    base_date = datetime(2026, 12, 1, 8, 0, 0)

    membre_role = MembreRole(
        membre_id=test_membre.id, role_code=test_role_comp.code  # DEV_PYTHON
    )
    session.add(membre_role)
    session.commit()

    # GIVEN: Utilisation stricte de PlanningFullCreate et SlotFullNested
    full_data = PlanningFullCreate(
        activite=ActiviteCreate(
            type="Culte",
            campus_id=str(test_campus.id),
            ministere_organisateur_id=str(test_ministere.id),
            date_debut=base_date,
            date_fin=base_date + timedelta(hours=3),
            lieu="Main Hall",
        ),
        planning=PlanningServiceCreate(
            statut_code="BROUILLON",
            activite_id="00000000-0000-0000-0000-000000000000",
            # Valeur factice, sera ignorée par le service
            # activite_id est maintenant optionnel dans PlanningServiceCreate
        ),
        slots=[
            SlotFullNested(
                nom_creneau="Louange",
                date_debut=base_date + timedelta(minutes=30),
                date_fin=base_date + timedelta(hours=1),
                affectations=[
                    AssignmentSimpleCreate(
                        membre_id=str(test_membre.id), role_code=test_role_comp.code
                    )
                ],
            )
        ],
    )

    # WHEN
    response = client.post(
        "/plannings/full",
        json=full_data.model_dump(mode="json", exclude_none=True),
        headers=admin_headers,
    )

    if response.status_code == 400:
        print(f"\nDETAIL ERREUR 400: {response.json()}")
    # THEN
    assert response.status_code == status.HTTP_201_CREATED
    session.expire_all()
    db_act = session.exec(select(Activite).where(Activite.type == "Culte")).first()
    assert db_act is not None
    # 2. Vérifier que le planning lié existe en utilisant activite_id
    # On cherche le planning qui pointe vers notre activité
    db_planning = session.exec(
        select(PlanningService).where(PlanningService.activite_id == db_act.id)
    ).first()

    assert db_planning is not None
    assert db_planning.statut_code == "BROUILLON"

    # 3. Vérifier qu'il y a bien un slot créé
    session.refresh(db_planning)
    assert len(db_planning.slots) == 1
    assert db_planning.slots[0].nom_creneau == "Louange"


def test_api_update_full_planning_sync_success(
    client, admin_headers, session, robust_data_factory
):
    # GIVEN
    original_planning = robust_data_factory(status="BROUILLON")
    session.commit()
    # On refresh pour charger les slots en DB dans l'objet de session
    session.refresh(original_planning)

    p_id = str(original_planning.id)
    slot_id_to_keep = str(original_planning.slots[0].id)

    # Payload de synchronisation
    update_data = {
        "activite": {"type": "Formation Sync"},
        "slots": [
            {
                "id": slot_id_to_keep,
                "nom_creneau": "Slot Gardé",
                "date_debut": original_planning.slots[0].date_debut.isoformat(),
                "date_fin": original_planning.slots[0].date_fin.isoformat(),
                "affectations": [],
            }
        ],
    }

    # WHEN
    response = client.patch(
        f"/plannings/{p_id}/full",
        json=update_data,
        headers=admin_headers,
    )

    # THEN
    assert response.status_code == status.HTTP_200_OK

    # CRITIQUE: On expire tout pour forcer un SELECT frais en DB
    session.expire_all()

    # On récupère le planning via une nouvelle requête
    db_planning = session.exec(
        select(PlanningService).where(PlanningService.id == original_planning.id)
    ).first()

    # On force le chargement des slots (lazy loading refresh)
    session.refresh(db_planning)

    # assert db_planning.activite.type == "Formation Sync"
    # # Si le service sync_planning_slots a bien fait son delete() + flush(), on aura 1.
    assert len(db_planning.slots) == 1


def test_api_update_full_conflict_rollback(
    client, admin_headers, session, robust_data_factory
):
    # GIVEN
    planning = robust_data_factory(status="BROUILLON")
    old_type = planning.activite.type
    planning_id = planning.id
    session.commit()

    conflict_data = PlanningFullUpdate(
        activite=ActiviteUpdate(type="ROLLBACK_TEST"),
        slots=[
            SlotFullUpdate(
                nom_creneau="Collision 1",
                date_debut=datetime(2026, 6, 1, 10, 0),
                date_fin=datetime(2026, 6, 1, 12, 0),
            ),
            SlotFullUpdate(
                nom_creneau="Collision 2",
                date_debut=datetime(2026, 6, 1, 11, 0),  # Collision
                date_fin=datetime(2026, 6, 1, 13, 0),
            ),
        ],
    )

    # WHEN
    response = client.patch(
        f"/plannings/{planning_id}/full",
        json=conflict_data.model_dump(mode="json"),
        headers=admin_headers,
    )

    # THEN
    assert response.status_code == status.HTTP_409_CONFLICT

    # IMPORTANT: Nettoyer la session après l'erreur 409 pour éviter PendingRollbackError
    session.rollback()

    db_act = session.exec(
        select(Activite).where(Activite.id == planning.activite_id)
    ).first()
    assert db_act.type == old_type

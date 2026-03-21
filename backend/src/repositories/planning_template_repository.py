"""Repository pour les templates de planning."""

from typing import List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import selectinload
from sqlmodel import Session, col, select

from models.schema_db_model import PlanningTemplate, PlanningTemplateSlot
from repositories.base_repository import BaseRepository


class PlanningTemplateRepository(BaseRepository[PlanningTemplate]):
    """CRUD repository pour PlanningTemplate."""

    def __init__(self, db: Session) -> None:
        super().__init__(db, PlanningTemplate)

    def get_with_slots(self, template_id: str) -> Optional[PlanningTemplate]:
        """Charge un template avec ses créneaux et rôles (évite N+1)."""
        stmt = (
            select(PlanningTemplate)
            .where(PlanningTemplate.id == template_id)
            .options(
                self._slot_roles_option(),
            )
        )
        return self.db.exec(stmt).first()

    def _slot_roles_option(self):  # type: ignore[return]
        """Retourne l'option eager-load slots → roles."""
        return selectinload(
            PlanningTemplate.slots  # type: ignore[arg-type]
        ).selectinload(
            PlanningTemplateSlot.roles  # type: ignore[arg-type]
        )

    def list_by_campus(self, campus_id: str) -> List[PlanningTemplate]:
        """Liste les templates d'un campus, triés par used_count DESC."""
        stmt = (
            select(PlanningTemplate)
            .where(PlanningTemplate.campus_id == campus_id)
            .options(self._slot_roles_option())
            .order_by(desc(col(PlanningTemplate.used_count)))
        )
        return list(self.db.exec(stmt).all())

    def list_by_ministere(self, ministere_id: str) -> List[PlanningTemplate]:
        """Liste les templates d'un ministère, triés par used_count DESC."""
        stmt = (
            select(PlanningTemplate)
            .where(PlanningTemplate.ministere_id == ministere_id)
            .options(self._slot_roles_option())
            .order_by(desc(col(PlanningTemplate.used_count)))
        )
        return list(self.db.exec(stmt).all())

    def increment_used_count(self, template_id: str) -> None:
        """Incrémente le compteur d'utilisation du template."""
        template = self.get_by_id(template_id)
        if template:
            template.used_count += 1
            self.db.add(template)
            self.db.flush()

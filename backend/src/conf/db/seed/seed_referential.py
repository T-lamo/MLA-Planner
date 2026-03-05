import logging
from datetime import date
from typing import Any, Dict, Type, TypeVar

from rich.console import Console
from rich.logging import RichHandler
from sqlmodel import Session, SQLModel, select

from conf.db.database import Database  # Adapter l'import selon ton projet
from models import (
    Campus,
    Ministere,
    OrganisationICC,
    Pays,
    Permission,
    Role,
    StatutAffectation,
    StatutPlanning,
    TypeResponsabilite,
)

# Configuration du Logger
console = Console()
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, console=console)],
)
logger = logging.getLogger("seed")

T = TypeVar("T", bound=SQLModel)


class SeedReferentials:
    def __init__(self, session: Session):
        self.session = session

    def get_or_create_upsert(
        self, model: Type[T], lookup_data: Dict[str, Any], update_data: Dict[str, Any]
    ) -> T:
        """Logique Idempotente : Récupère/Met à jour ou crée."""
        statement = select(model)
        for key, value in lookup_data.items():
            statement = statement.where(getattr(model, key) == value)

        instance = self.session.exec(statement).first()

        if instance:
            updated = False
            for key, value in update_data.items():
                if getattr(instance, key) != value:
                    setattr(instance, key, value)
                    updated = True
            if updated:
                self.session.add(instance)
                logger.info(f"[yellow][UPDATE][/yellow] {model.__name__}")
            else:
                logger.info(f"[green][OK][/green] {model.__name__}")
            return instance

        new_instance = model(**lookup_data, **update_data)
        self.session.add(new_instance)
        self.session.flush()
        logger.info(f"[cyan][NEW][/cyan] {model.__name__}")
        return new_instance

    def run(self) -> None:
        try:
            # --- GROUPE A : Enums ---
            for c in ["BROUILLON", "PUBLIE", "ANNULE", "TERMINE"]:
                self.get_or_create_upsert(StatutPlanning, {"code": c}, {})

            for c in ["PROPOSE", "CONFIRME", "REFUSE", "PRESENT", "ABSENT"]:
                self.get_or_create_upsert(StatutAffectation, {"code": c}, {})

            for c in ["RESPONSABLE", "ADJOINT", "MEMBRE_ACTIF"]:
                self.get_or_create_upsert(TypeResponsabilite, {"code": c}, {})

            # --- GROUPE B : Sécurité (Correction F841: suppression p_admin) ---
            self.get_or_create_upsert(
                Permission, {"code": "ALL_ACCESS"}, {"nom": "Accès Total"}
            )
            self.get_or_create_upsert(Role, {"id": "ADMIN_ID"}, {"nom": "Admin"})
            self.get_or_create_upsert(Role, {"id": "MEMBRE_ID"}, {"nom": "Membre"})

            # --- GROUPE C : Hiérarchie (Correction E501: split des lignes) ---
            org = self.get_or_create_upsert(
                OrganisationICC,
                {"id": "ICC_WORLD"},
                {"nom": "ICC World", "date_creation": date(2020, 1, 1)},
            )

            pays_fr = self.get_or_create_upsert(
                Pays, {"nom": "FRANCE"}, {"code": "FR", "organisation_id": org.id}
            )

            campus_tls = self.get_or_create_upsert(
                Campus,
                {"nom": "Toulouse"},
                {
                    "ville": "Toulouse",
                    "pays_id": pays_fr.id,
                    "timezone": "Europe/Paris",
                },
            )

            # --- NOUVELLE LOGIQUE MANY-TO-MANY MINISTÈRES ---
            for min_nom in ["MLA", "ACCUEIL", "MFI", "INTERCESSION"]:
                ministere = self.get_or_create_upsert(
                    Ministere,
                    {"nom": min_nom},
                    {"date_creation": "2024-01-01", "actif": True},
                )
                # On s'assure que le ministère est lié au campus de Toulouse
                if campus_tls not in ministere.campuses:
                    ministere.campuses.append(campus_tls)
                    self.session.add(ministere)

            # --- GROUPE D : Métier ---
            # cat_chant = self.get_or_create_upsert(CategorieRole, {"nom": "Chant"}, {})

            # voix_list = ["SOPRANO", "ALTO", "TENOR", "BARYTON", "BASSE", "LEAD"]
            # for voix in voix_list:
            #     self.get_or_create_upsert(
            #         RoleCompetence, {"nom": voix}, {"categorie_id": cat_chant.id}
            #     )

            # self.session.commit()
            # logger.info("\n[bold green]✅ Seeding terminé ![/bold green]")

        except Exception as e:
            self.session.rollback()
            logger.error(f"[bold red]❌ Erreur :[/bold red] {e}")
            raise


def main() -> None:

    with Session(Database.get_engine()) as session:
        seeder = SeedReferentials(session)
        seeder.run()


if __name__ == "__main__":
    main()

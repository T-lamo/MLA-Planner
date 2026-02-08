from typing import cast

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from core.exceptions.exceptions import BadRequestException
from models import Musicien, MusicienCreate, MusicienRead, MusicienUpdate
from repositories.musicien_repository import MusicienRepository

from .base_service import BaseService


class MusicienService(
    BaseService[MusicienCreate, MusicienRead, MusicienUpdate, Musicien]
):
    def __init__(self, db: Session):
        super().__init__(MusicienRepository(db), "Musicien")
        self.db = db
        self.musicien_repo = cast(MusicienRepository, self.repo)

    def create(self, data: MusicienCreate) -> Musicien:
        """Crée un musicien et ses instruments de manière atomique."""
        try:
            db_obj = Musicien(chantre_id=data.chantre_id)
            self.db.add(db_obj)
            self.db.flush()

            for inst in data.instruments_in:
                self.musicien_repo.add_instrument_link(
                    db_obj.id, inst.instrument_id, inst.is_principal
                )

            self.db.commit()
            self.db.refresh(db_obj)
            return db_obj
        except IntegrityError as exc:
            self.db.rollback()
            raise BadRequestException(
                "Erreur d'intégrité : Le chantre ou l'instrument est invalide."
            ) from exc

    def update(self, identifiant: str, data: MusicienUpdate) -> Musicien:
        """Met à jour un musicien et synchronise ses instruments."""
        db_obj = self.get_one(identifiant)
        update_dict = data.model_dump(exclude_unset=True)

        try:
            # Logique de synchronisation des instruments
            if "instruments_in" in update_dict and data.instruments_in is not None:
                # 1. Nettoyage des anciennes liaisons
                self.musicien_repo.delete_instruments_by_musicien(db_obj.id)

                # 2. Ajout des nouvelles liaisons
                for inst in data.instruments_in:
                    self.musicien_repo.add_instrument_link(
                        db_obj.id, inst.instrument_id, inst.is_principal
                    )
                del update_dict["instruments_in"]

            # Mise à jour des autres champs via le repository de base
            # Note: Le repo.update effectue déjà un commit/refresh
            return self.repo.update(db_obj, update_dict)

        except IntegrityError as exc:
            self.db.rollback()
            raise BadRequestException(
                "Mise à jour impossible : violation d'intégrité (ID invalide)."
            ) from exc

"""
Service du module Songbook.

Contient :
  ChordTransposer         — transposition de grilles ChordPro (lru_cache)
  ChantCategorieService   — CRUD des catégories de chants
  ChantService            — CRUD des chants + gestion du contenu versionné
"""

import re
from datetime import datetime, timezone
from functools import lru_cache
from typing import List, Optional, Tuple

from sqlalchemy import func, nullslast
from sqlmodel import Session, col, select

from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
from models.chant_model import (
    Chant,
    ChantCategorie,
    ChantCategorieCreate,
    ChantCategorieUpdate,
    ChantContenu,
    ChantContenuCreate,
    ChantContenuUpdate,
    ChantCreate,
    ChantRead,
    ChantReadFull,
    ChantUpdate,
)

# ---------------------------------------------------------------------------
# ChordTransposer
# ---------------------------------------------------------------------------

_CHROMATIC = [
    "C",
    "C#",
    "D",
    "D#",
    "E",
    "F",
    "F#",
    "G",
    "G#",
    "A",
    "A#",
    "B",
]
_ENHARMONICS = {
    "Db": "C#",
    "Eb": "D#",
    "Fb": "E",
    "Gb": "F#",
    "Ab": "G#",
    "Bb": "A#",
    "Cb": "B",
}
_CHORD_RE = re.compile(r"\[([A-G][b#]?(?:m|maj|min|dim|aug|sus|add)?[0-9]*)\]")


@lru_cache(maxsize=256)
def _cached_transpose(chord_root: str, semitones: int) -> str:
    """Transpose une note racine de `semitones` demi-tons (cachée)."""
    normalized = _ENHARMONICS.get(chord_root, chord_root)
    if normalized not in _CHROMATIC:
        return chord_root
    idx = (_CHROMATIC.index(normalized) + semitones) % 12
    return _CHROMATIC[idx]


class ChordTransposer:
    """Transpose les grilles ChordPro sans dépendance externe."""

    def transpose_chord(self, chord: str, semitones: int) -> str:
        """Transpose une grille (ex: 'Am7') de N demi-tons."""
        match = re.match(r"^([A-G][b#]?)(.*)", chord)
        if not match:
            return chord
        root, suffix = match.group(1), match.group(2)
        new_root = _cached_transpose(root, semitones)
        return f"{new_root}{suffix}"

    def transpose_content(self, content: str, semitones: int) -> str:
        """Remplace tous les [Accord] dans un texte ChordPro."""
        if semitones == 0:
            return content

        def _replace(m: re.Match) -> str:  # type: ignore[type-arg]
            return f"[{self.transpose_chord(m.group(1), semitones)}]"

        return _CHORD_RE.sub(_replace, content)

    def transpose_tonalite(self, tonalite: str, semitones: int) -> str:
        """Transpose la tonalité principale (ex: 'G' -> 'A')."""
        match = re.match(r"^([A-G][b#]?)(.*)", tonalite)
        if not match:
            return tonalite
        root, suffix = match.group(1), match.group(2)
        return f"{_cached_transpose(root, semitones)}{suffix}"


# ---------------------------------------------------------------------------
# ChantCategorieService
# ---------------------------------------------------------------------------


class ChantCategorieService:
    """CRUD des catégories de chants."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_categories(self) -> List[ChantCategorie]:
        """Liste toutes les catégories triées par ordre."""
        stmt = select(ChantCategorie).order_by(
            col(ChantCategorie.ordre), col(ChantCategorie.libelle)
        )
        return list(self.db.exec(stmt).all())

    def get_categorie(self, code: str) -> ChantCategorie:
        """Retourne une catégorie ou lève SONG_CAT_NOT_FOUND."""
        cat = self.db.get(ChantCategorie, code.strip().upper())
        if not cat:
            raise AppException(ErrorRegistry.SONG_CAT_NOT_FOUND)
        return cat

    def create_categorie(self, payload: ChantCategorieCreate) -> ChantCategorie:
        """Crée une catégorie — lève SONG_CAT_DUPLICATE si le code existe."""
        normalized = payload.code.strip().upper()
        if self.db.get(ChantCategorie, normalized):
            raise AppException(ErrorRegistry.SONG_CAT_DUPLICATE)
        cat = ChantCategorie(
            code=normalized,
            libelle=payload.libelle,
            ordre=payload.ordre,
            description=payload.description,
        )
        self.db.add(cat)
        self.db.flush()
        self.db.refresh(cat)
        return cat

    def update_categorie(
        self, code: str, payload: ChantCategorieUpdate
    ) -> ChantCategorie:
        """Met à jour partiellement une catégorie."""
        cat = self.get_categorie(code)
        if payload.libelle is not None:
            cat.libelle = payload.libelle
        if payload.ordre is not None:
            cat.ordre = payload.ordre
        if payload.description is not None:
            cat.description = payload.description
        self.db.add(cat)
        self.db.flush()
        self.db.refresh(cat)
        return cat

    def delete_categorie(self, code: str) -> None:
        """Supprime une catégorie vide — lève SONG_CAT_HAS_CHANTS sinon."""
        cat = self.get_categorie(code)
        count = len(cat.chants) if cat.chants else 0
        if count > 0:
            raise AppException(ErrorRegistry.SONG_CAT_HAS_CHANTS, count=count)
        self.db.delete(cat)
        self.db.flush()


# ---------------------------------------------------------------------------
# ChantService
# ---------------------------------------------------------------------------


class ChantService:
    """CRUD des chants et gestion du contenu ChordPro versionné."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self._transposer = ChordTransposer()

    # ------------------------------------------------------------------ #
    #  Helpers privés
    # ------------------------------------------------------------------ #

    def _get_chant(self, chant_id: str) -> Chant:
        chant = self.db.get(Chant, chant_id)
        if not chant or chant.deleted_at is not None:
            raise AppException(ErrorRegistry.SONG_NOT_FOUND)
        return chant

    def _build_chant_read(self, chant: Chant) -> ChantRead:
        return ChantRead.model_validate(chant)

    # ------------------------------------------------------------------ #
    #  CRUD Chants
    # ------------------------------------------------------------------ #

    def list_chants(
        self,
        *,
        campus_id: Optional[str] = None,
        categorie_code: Optional[str] = None,
        artiste: Optional[str] = None,
        q: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[ChantRead], int]:
        """Liste paginée des chants — filtrée par campus (multi-tenant)."""
        stmt = select(Chant).where(
            Chant.deleted_at == None,  # noqa: E711
            Chant.actif == True,  # noqa: E712
        )
        if campus_id is not None:
            stmt = stmt.where(Chant.campus_id == campus_id)
        if categorie_code:
            stmt = stmt.where(Chant.categorie_code == categorie_code)
        # pylint: disable=no-member
        if artiste:
            stmt = stmt.where(col(Chant.artiste).ilike(f"%{artiste}%"))
        if q:
            stmt = stmt.where(col(Chant.titre).ilike(f"%{q}%"))
        # pylint: enable=no-member
        # Compte total avant pagination
        count_stmt = select(func.count()).select_from(  # pylint: disable=not-callable
            stmt.subquery()
        )
        total: int = self.db.exec(count_stmt).one()  # type: ignore[assignment]
        # Tri : artiste NULLS LAST, puis titre, puis pagination
        paginated = (
            stmt.order_by(nullslast(col(Chant.artiste)), col(Chant.titre))
            .offset(offset)
            .limit(limit)
        )
        items = list(self.db.exec(paginated).all())
        return [ChantRead.model_validate(c) for c in items], total

    def get_chant_full(self, chant_id: str) -> ChantReadFull:
        """Retourne un chant avec son contenu et sa catégorie."""
        chant = self._get_chant(chant_id)
        return ChantReadFull.model_validate(chant)

    def create_chant(self, payload: ChantCreate) -> ChantRead:
        """Crée un chant."""
        chant = Chant(
            titre=payload.titre,
            artiste=payload.artiste,
            campus_id=payload.campus_id,
            categorie_code=payload.categorie_code,
            youtube_url=payload.youtube_url,
        )
        self.db.add(chant)
        self.db.flush()
        self.db.refresh(chant)
        return ChantRead.model_validate(chant)

    def update_chant(self, chant_id: str, payload: ChantUpdate) -> ChantRead:
        """Met à jour partiellement un chant."""
        chant = self._get_chant(chant_id)
        if payload.titre is not None:
            chant.titre = payload.titre
        if payload.artiste is not None:
            chant.artiste = payload.artiste
        if payload.categorie_code is not None:
            chant.categorie_code = payload.categorie_code
        if payload.youtube_url is not None:
            chant.youtube_url = payload.youtube_url
        self.db.add(chant)
        self.db.flush()
        self.db.refresh(chant)
        return ChantRead.model_validate(chant)

    def delete_chant(self, chant_id: str) -> None:
        """Soft-delete d'un chant."""
        chant = self._get_chant(chant_id)
        chant.deleted_at = datetime.now(timezone.utc)
        chant.actif = False
        self.db.add(chant)
        self.db.flush()

    # ------------------------------------------------------------------ #
    #  Contenu ChordPro
    # ------------------------------------------------------------------ #

    def get_contenu(self, chant_id: str) -> ChantContenu:
        """Retourne le contenu ChordPro d'un chant."""
        self._get_chant(chant_id)
        stmt = select(ChantContenu).where(ChantContenu.chant_id == chant_id)
        contenu = self.db.exec(stmt).first()
        if not contenu:
            raise AppException(ErrorRegistry.SONG_NOT_FOUND)
        return contenu

    def upsert_contenu(
        self, chant_id: str, payload: ChantContenuCreate
    ) -> ChantContenu:
        """Crée ou remplace le contenu ChordPro (sans verrou OCC)."""
        self._get_chant(chant_id)
        stmt = select(ChantContenu).where(ChantContenu.chant_id == chant_id)
        existing = self.db.exec(stmt).first()
        if existing:
            existing.tonalite = payload.tonalite
            existing.paroles_chords = payload.paroles_chords
            existing.version += 1
            existing.date_modification = datetime.now(timezone.utc)
            self.db.add(existing)
            self.db.flush()
            self.db.refresh(existing)
            return existing
        contenu = ChantContenu(
            chant_id=chant_id,
            tonalite=payload.tonalite,
            paroles_chords=payload.paroles_chords,
        )
        self.db.add(contenu)
        self.db.flush()
        self.db.refresh(contenu)
        return contenu

    def update_contenu(
        self, chant_id: str, payload: ChantContenuUpdate
    ) -> ChantContenu:
        """Met à jour le contenu avec verrou optimiste (OCC)."""
        contenu = self.get_contenu(chant_id)
        if contenu.version != payload.version:
            raise AppException(
                ErrorRegistry.SONG_CONTENT_VERSION_CONFLICT,
                expected=contenu.version,
                received=payload.version,
            )
        if payload.tonalite is not None:
            contenu.tonalite = payload.tonalite
        if payload.paroles_chords is not None:
            contenu.paroles_chords = payload.paroles_chords
        contenu.version += 1
        contenu.date_modification = datetime.now(timezone.utc)
        self.db.add(contenu)
        self.db.flush()
        self.db.refresh(contenu)
        return contenu

    # ------------------------------------------------------------------ #
    #  Transposition (sans sauvegarde)
    # ------------------------------------------------------------------ #

    def transpose(self, chant_id: str, semitones: int) -> Tuple[str, str, str]:
        """Transpose le contenu et retourne (tonalite_orig, tonalite_new, paroles)."""
        contenu = self.get_contenu(chant_id)
        new_tonalite = self._transposer.transpose_tonalite(contenu.tonalite, semitones)
        new_paroles = self._transposer.transpose_content(
            contenu.paroles_chords, semitones
        )
        return contenu.tonalite, new_tonalite, new_paroles

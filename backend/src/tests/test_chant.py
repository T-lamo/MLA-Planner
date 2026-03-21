"""
Tests du module Songbook (chants, catégories, contenu, transposition).

Fixtures utilisées :
  session   — depuis tests/fixtures/core.py
  client    — depuis tests/fixtures/core.py
  test_campus — depuis tests/fixtures/geo.py
"""

from uuid import uuid4

import pytest
from sqlmodel import Session

from core.exceptions.app_exception import AppException
from models.chant_model import (
    Chant,
    ChantCategorie,
    ChantCategorieCreate,
    ChantCategorieUpdate,
    ChantContenu,
    ChantContenuCreate,
    ChantContenuUpdate,
    ChantCreate,
    ChantUpdate,
)
from models.schema_db_model import Campus
from services.chant_service import ChantCategorieService, ChantService, ChordTransposer

# pylint: disable=redefined-outer-name


# ------------------------------------------------------------------ #
#  Fixtures locales
# ------------------------------------------------------------------ #


@pytest.fixture
def cat_svc(session: Session) -> ChantCategorieService:
    return ChantCategorieService(session)


@pytest.fixture
def chant_svc(session: Session) -> ChantService:
    return ChantService(session)


@pytest.fixture
def test_categorie(session: Session, cat_svc: ChantCategorieService) -> ChantCategorie:
    payload = ChantCategorieCreate(
        code=f"CAT{str(uuid4())[:4].upper()}",
        libelle="Gospel Test",
        ordre=1,
    )
    return cat_svc.create_categorie(payload)


@pytest.fixture
def test_chant(
    session: Session,
    chant_svc: ChantService,
    test_campus: Campus,
    test_categorie: ChantCategorie,
) -> Chant:
    payload = ChantCreate(
        titre="Amazing Grace",
        artiste="John Newton",
        campus_id=str(test_campus.id),
        categorie_code=test_categorie.code,
    )
    read = chant_svc.create_chant(payload)
    chant = session.get(Chant, read.id)
    assert chant is not None
    return chant


@pytest.fixture
def test_contenu(
    session: Session,
    chant_svc: ChantService,
    test_chant: Chant,
) -> ChantContenu:
    payload = ChantContenuCreate(
        tonalite="G",
        paroles_chords="[G]Amazing [C]grace [G]how [D]sweet the [G]sound",
    )
    contenu = chant_svc.upsert_contenu(str(test_chant.id), payload)
    return contenu


# ------------------------------------------------------------------ #
#  ChordTransposer
# ------------------------------------------------------------------ #


def test_transpose_simple_chord() -> None:
    """C transposé de 2 demi-tons = D."""
    t = ChordTransposer()
    assert t.transpose_chord("C", 2) == "D"


def test_transpose_minor_chord() -> None:
    """Am transposé de 3 = Cm."""
    t = ChordTransposer()
    assert t.transpose_chord("Am", 3) == "Cm"


def test_transpose_wrap_around() -> None:
    """B transposé de 1 = C (boucle sur 12)."""
    t = ChordTransposer()
    assert t.transpose_chord("B", 1) == "C"


def test_transpose_negative() -> None:
    """C transposé de -1 = B."""
    t = ChordTransposer()
    assert t.transpose_chord("C", -1) == "B"


def test_transpose_enharmonic() -> None:
    """Bb (enharmonique de A#) transposé de 2 = C."""
    t = ChordTransposer()
    assert t.transpose_chord("Bb", 2) == "C"


def test_transpose_content_replaces_all() -> None:
    """transpose_content remplace tous les accords dans le texte."""
    t = ChordTransposer()
    content = "[G]Loue [Em]le [C]Seigneur [D]"
    result = t.transpose_content(content, 2)
    assert "[A]" in result
    assert "[F#m]" in result
    assert "[D]" in result
    assert "[E]" in result


def test_transpose_zero_unchanged() -> None:
    """0 demi-ton = contenu inchangé."""
    t = ChordTransposer()
    content = "[G]Hello [Am]world"
    assert t.transpose_content(content, 0) == content


def test_transpose_tonalite() -> None:
    """Tonalité G transposée de 5 = C."""
    t = ChordTransposer()
    assert t.transpose_tonalite("G", 5) == "C"


# ------------------------------------------------------------------ #
#  ChantCategorieService
# ------------------------------------------------------------------ #


def test_create_categorie(cat_svc: ChantCategorieService) -> None:
    """Création d'une catégorie retourne le bon libellé."""
    payload = ChantCategorieCreate(
        code=f"TST{str(uuid4())[:4].upper()}",
        libelle="Cantique",
        ordre=5,
    )
    cat = cat_svc.create_categorie(payload)
    assert cat.libelle == "Cantique"
    assert cat.ordre == 5


def test_create_categorie_duplicate(
    cat_svc: ChantCategorieService,
    test_categorie: ChantCategorie,
) -> None:
    """Créer deux catégories avec le même code lève SONG_002."""
    payload = ChantCategorieCreate(
        code=test_categorie.code,
        libelle="Autre",
        ordre=0,
    )
    with pytest.raises(AppException) as exc_info:
        cat_svc.create_categorie(payload)
    assert exc_info.value.detail.code == "SONG_002"


def test_list_categories_ordered(cat_svc: ChantCategorieService) -> None:
    """Les catégories sont retournées triées par ordre."""
    for i, label in enumerate(["Louange", "Gospel", "Adoration"]):
        cat_svc.create_categorie(
            ChantCategorieCreate(
                code=f"ORD{i}{str(uuid4())[:3].upper()}",
                libelle=label,
                ordre=i,
            )
        )
    cats = cat_svc.list_categories()
    orders = [c.ordre for c in cats]
    assert orders == sorted(orders)


def test_update_categorie(
    cat_svc: ChantCategorieService,
    test_categorie: ChantCategorie,
) -> None:
    """Mise à jour partielle d'une catégorie."""
    updated = cat_svc.update_categorie(
        test_categorie.code, ChantCategorieUpdate(libelle="Gospel Updated")
    )
    assert updated.libelle == "Gospel Updated"


def test_delete_categorie_not_found(cat_svc: ChantCategorieService) -> None:
    """Supprimer une catégorie inexistante lève SONG_001."""
    with pytest.raises(AppException) as exc_info:
        cat_svc.delete_categorie("INEXISTANT_999")
    assert exc_info.value.detail.code == "SONG_001"


def test_delete_categorie_with_chants(
    cat_svc: ChantCategorieService,
    test_chant: Chant,
    test_categorie: ChantCategorie,
) -> None:
    """Supprimer une catégorie non vide lève SONG_003."""
    with pytest.raises(AppException) as exc_info:
        cat_svc.delete_categorie(test_categorie.code)
    assert exc_info.value.detail.code == "SONG_003"


# ------------------------------------------------------------------ #
#  ChantService — CRUD
# ------------------------------------------------------------------ #


def test_create_chant(
    chant_svc: ChantService,
    test_campus: Campus,
) -> None:
    """Création d'un chant retourne les champs corrects."""
    payload = ChantCreate(
        titre="Notre Dieu est grand",
        artiste="Chris Tomlin",
        campus_id=str(test_campus.id),
    )
    read = chant_svc.create_chant(payload)
    assert read.titre == "Notre Dieu est grand"
    assert read.artiste == "Chris Tomlin"
    assert read.actif is True


def test_get_chant_full(
    chant_svc: ChantService,
    test_chant: Chant,
    test_contenu: ChantContenu,
) -> None:
    """get_chant_full retourne le chant avec son contenu."""
    full = chant_svc.get_chant_full(str(test_chant.id))
    assert full.id == str(test_chant.id)
    assert full.contenu is not None
    assert full.contenu.tonalite == "G"


def test_update_chant(
    chant_svc: ChantService,
    test_chant: Chant,
) -> None:
    """Mise à jour partielle d'un chant."""
    updated = chant_svc.update_chant(
        str(test_chant.id),
        ChantUpdate(titre="Amazing Grace (Updated)"),
    )
    assert updated.titre == "Amazing Grace (Updated)"


def test_delete_chant(
    chant_svc: ChantService,
    test_chant: Chant,
) -> None:
    """Soft delete — le chant disparaît des résultats."""
    chant_svc.delete_chant(str(test_chant.id))
    with pytest.raises(AppException) as exc_info:
        chant_svc.get_chant_full(str(test_chant.id))
    assert exc_info.value.detail.code == "SONG_004"


def test_list_chants_by_campus(
    chant_svc: ChantService,
    test_campus: Campus,
    test_chant: Chant,
) -> None:
    """list_chants filtre correctement par campus."""
    items, total = chant_svc.list_chants(campus_id=str(test_campus.id))
    assert total >= 1
    ids = [c.id for c in items]
    assert str(test_chant.id) in ids


def test_list_chants_wrong_campus(
    chant_svc: ChantService,
    test_chant: Chant,
) -> None:
    """Un campus différent ne voit pas les chants des autres."""
    items, total = chant_svc.list_chants(campus_id=str(uuid4()))
    assert total == 0
    assert items == []


def test_list_chants_search(
    chant_svc: ChantService,
    test_campus: Campus,
    test_chant: Chant,
) -> None:
    """Recherche par titre fonctionne (case-insensitive)."""
    items, _ = chant_svc.list_chants(campus_id=str(test_campus.id), q="amazing")
    assert any(c.id == str(test_chant.id) for c in items)


# ------------------------------------------------------------------ #
#  ChantService — Contenu
# ------------------------------------------------------------------ #


def test_upsert_contenu_creates(
    chant_svc: ChantService,
    test_chant: Chant,
) -> None:
    """upsert_contenu crée le contenu si absent."""
    payload = ChantContenuCreate(
        tonalite="D",
        paroles_chords="[D]Test [G]chord",
    )
    contenu = chant_svc.upsert_contenu(str(test_chant.id), payload)
    assert contenu.tonalite == "D"
    assert contenu.version == 1


def test_upsert_contenu_updates(
    chant_svc: ChantService,
    test_chant: Chant,
    test_contenu: ChantContenu,
) -> None:
    """upsert_contenu incrémente la version si contenu existant."""
    version_before = test_contenu.version  # capturer avant mutation
    payload = ChantContenuCreate(
        tonalite="A",
        paroles_chords="[A]New [E]chords",
    )
    updated = chant_svc.upsert_contenu(str(test_chant.id), payload)
    assert updated.tonalite == "A"
    assert updated.version == version_before + 1


def test_update_contenu_version_conflict(
    chant_svc: ChantService,
    test_chant: Chant,
    test_contenu: ChantContenu,
) -> None:
    """Mauvaise version lève SONG_006."""
    payload = ChantContenuUpdate(
        tonalite="E",
        version=999,
    )
    with pytest.raises(AppException) as exc_info:
        chant_svc.update_contenu(str(test_chant.id), payload)
    assert exc_info.value.detail.code == "SONG_006"


def test_update_contenu_ok(
    chant_svc: ChantService,
    test_chant: Chant,
    test_contenu: ChantContenu,
) -> None:
    """Mise à jour avec la bonne version incrémente correctement."""
    version_before = test_contenu.version  # capturer avant mutation
    payload = ChantContenuUpdate(
        tonalite="Am",
        version=version_before,
    )
    updated = chant_svc.update_contenu(str(test_chant.id), payload)
    assert updated.tonalite == "Am"
    assert updated.version == version_before + 1


# ------------------------------------------------------------------ #
#  ChantService — Transposition
# ------------------------------------------------------------------ #


def test_transpose_endpoint(
    chant_svc: ChantService,
    test_chant: Chant,
    test_contenu: ChantContenu,
) -> None:
    """Transposition retourne les bonnes tonalités sans sauvegarder."""
    orig, new_ton, new_paroles = chant_svc.transpose(str(test_chant.id), semitones=2)
    assert orig == "G"
    assert new_ton == "A"
    assert "[A]" in new_paroles


def test_transpose_does_not_save(
    chant_svc: ChantService,
    test_chant: Chant,
    test_contenu: ChantContenu,
) -> None:
    """La transposition ne modifie pas la DB."""
    version_before = test_contenu.version
    chant_svc.transpose(str(test_chant.id), semitones=5)
    reloaded = chant_svc.get_contenu(str(test_chant.id))
    assert reloaded.version == version_before
    assert reloaded.tonalite == "G"

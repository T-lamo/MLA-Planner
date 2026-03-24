"""Schémas pour la génération de plannings en série (US-98)."""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import List, Optional

from sqlmodel import SQLModel


class SerieRecurrence(str, Enum):
    """Type de récurrence d'une série de plannings."""

    HEBDOMADAIRE = "HEBDOMADAIRE"
    MENSUELLE = "MENSUELLE"


class GenerateSeriesPreviewRequest(SQLModel):
    """Payload prévisualisation d'une série."""

    date_debut: date
    date_fin: date
    recurrence: SerieRecurrence
    jour_semaine: Optional[int] = None  # 0=lundi … 6=dimanche


class GenerateSeriesRequest(GenerateSeriesPreviewRequest):
    """Payload génération d'une série (prévisualisation + template_id)."""

    template_id: str


class ConflitDate(SQLModel):
    """Planning existant sur une date cible."""

    date: date
    planning_id: str
    planning_titre: str


class SeriesPreviewResponse(SQLModel):
    """Résultat de la prévisualisation : dates calculées + conflits."""

    dates: List[date]
    total: int
    conflits: List[ConflitDate]


class PlanningSerieItem(SQLModel):
    """Planning créé dans une série."""

    id: str
    titre: str
    date_debut: date
    statut: str


class GenerateSeriesResponse(SQLModel):
    """Résultat de la génération : identifiant de série + plannings créés."""

    serie_id: str
    total: int
    plannings: List[PlanningSerieItem]

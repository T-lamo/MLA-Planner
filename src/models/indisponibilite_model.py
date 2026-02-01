from typing import Optional

from pydantic import ConfigDict, field_validator, model_validator
from sqlmodel import Field, SQLModel

from .chantre_model import ChantreRead


# -------------------------
# BASE
# -------------------------
class IndisponibiliteBase(SQLModel):
    dateDebut: Optional[str] = Field(
        default=None,
        description="Date de début d'indisponibilité (format ISO YYYY-MM-DD)",
    )
    dateFin: Optional[str] = Field(
        default=None,
        description="Date de fin d'indisponibilité (format ISO YYYY-MM-DD)",
    )
    motif: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Motif de l'indisponibilité",
    )
    validee: bool = Field(
        default=False, description="Indique si l'indisponibilité est validée"
    )

    # ======================
    # VALIDATION CHAMPS
    # ======================
    @field_validator("dateDebut", "dateFin")
    @classmethod
    def validate_date_iso(cls, v: Optional[str]):
        if v is None:
            return v
        try:
            parts = v.split("-")
            if len(parts) != 3:
                raise ValueError
            year, month, day = map(int, parts)
            if not (1 <= month <= 12 and 1 <= day <= 31 and year > 1900):
                raise ValueError
        except Exception as e:
            raise ValueError("Les dates doivent respecter le format YYYY-MM-DD") from e
        return v

    # ======================
    # VALIDATION METIER
    # ======================
    @model_validator(mode="after")
    def validate_date_range(self):
        if self.dateDebut and self.dateFin:
            if self.dateFin < self.dateDebut:
                raise ValueError("dateFin doit être postérieure ou égale à dateDebut")
        return self


# -------------------------
# CREATE
# -------------------------
class IndisponibiliteCreate(IndisponibiliteBase):
    chantre_id: str = Field(
        min_length=36,
        max_length=36,
        description="UUID du chantre concerné",
    )


# -------------------------
# READ
# -------------------------
class IndisponibiliteRead(IndisponibiliteBase):
    id: str
    chantre: Optional["ChantreRead"] = None
    model_config = ConfigDict(from_attributes=True)  # type: ignore


# -------------------------
# UPDATE
# -------------------------
class IndisponibiliteUpdate(SQLModel):
    dateDebut: Optional[str] = None
    dateFin: Optional[str] = None
    motif: Optional[str] = None
    validee: Optional[bool] = None

    @field_validator("dateDebut", "dateFin")
    @classmethod
    def validate_date_iso(cls, v: Optional[str]):
        if v is None:
            return v
        try:
            parts = v.split("-")
            if len(parts) != 3:
                raise ValueError
            year, month, day = map(int, parts)
            if not (1 <= month <= 12 and 1 <= day <= 31 and year > 1900):
                raise ValueError
        except Exception as e:
            raise ValueError("Les dates doivent respecter le format YYYY-MM-DD") from e
        return v

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.dateDebut and self.dateFin:
            if self.dateFin < self.dateDebut:
                raise ValueError("dateFin doit être postérieure ou égale à dateDebut")
        return self


__all__ = [
    "IndisponibiliteBase",
    "IndisponibiliteCreate",
    "IndisponibiliteRead",
    "IndisponibiliteUpdate",
]

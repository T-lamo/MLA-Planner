from typing import Optional

from pydantic import ConfigDict, field_validator, model_validator
from sqlmodel import Field, SQLModel


# -------------------------
# BASE
# -------------------------
class IndisponibiliteBase(SQLModel):
    date_debut: Optional[str] = Field(
        default=None,
        description="Date de début d'indisponibilité (format ISO YYYY-MM-DD)",
    )
    date_fin: Optional[str] = Field(
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

    @field_validator("date_debut", "date_fin")
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
        except Exception as exc:
            raise ValueError(
                "Les dates doivent respecter le format YYYY-MM-DD"
            ) from exc
        return v

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.date_debut and self.date_fin:
            if self.date_fin < self.date_debut:
                raise ValueError("date_fin doit être postérieure ou égale à date_debut")
        return self


# -------------------------
# CREATE
# -------------------------
class IndisponibiliteCreate(IndisponibiliteBase):
    membre_id: str = Field(description="UUID du membre concerné")


# -------------------------
# READ
# -------------------------
class IndisponibiliteRead(IndisponibiliteBase):
    id: str
    membre_id: str  # Ajouté pour la lecture complète
    model_config = ConfigDict(from_attributes=True)  # type: ignore


# -------------------------
# UPDATE
# -------------------------
class IndisponibiliteUpdate(SQLModel):
    date_debut: Optional[str] = None
    date_fin: Optional[str] = None
    motif: Optional[str] = None
    validee: Optional[bool] = None

    @field_validator("date_debut", "date_fin")
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
        except Exception as exc:
            raise ValueError(
                "Les dates doivent respecter le format YYYY-MM-DD"
            ) from exc
        return v

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.date_debut and self.date_fin:
            if self.date_fin < self.date_debut:
                raise ValueError("date_fin doit être postérieure ou égale à date_debut")
        return self


__all__ = [
    "IndisponibiliteBase",
    "IndisponibiliteCreate",
    "IndisponibiliteRead",
    "IndisponibiliteUpdate",
]

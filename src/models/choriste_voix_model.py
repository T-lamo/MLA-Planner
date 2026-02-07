from sqlmodel import Field, SQLModel


# -------------------------
# CHORISTE-VOIX (Liaison)
# -------------------------
class ChoristeVoixBase(SQLModel):
    voix_code: str = Field(description="Code unique de la voix (ex: TENOR, ALTO)")
    is_principal: bool = Field(
        default=False, description="Définit si c'est la voix principale"
    )


class ChoristeVoixCreate(ChoristeVoixBase):
    pass


class ChoristeVoixRead(ChoristeVoixBase):
    # On ne renvoie pas forcément choriste_id ici car c'est imbriqué dans Choriste
    pass


__all__ = ["ChoristeVoixBase", "ChoristeVoixCreate", "ChoristeVoixRead"]

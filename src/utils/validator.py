from pydantic import field_validator


class NotBlankFieldsMixin:
    """
    Mixin générique pour vérifier que certains champs string
    ne sont pas vides après strip().
    """

    __not_blank_fields__: tuple[str, ...] = ()

    @field_validator("*", mode="before")
    @classmethod
    def check_not_blank(cls, v, info):
        if info.field_name not in cls.__not_blank_fields__:
            return v

        if v is None:
            return v

        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError(f"Le champ '{info.field_name}' ne peut pas être vide")
        return v

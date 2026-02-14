from pydantic import ValidationError, field_validator


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


def parse_pydantic_errors(model_name: str, e: ValidationError):
    """Génère un message d'erreur lisible pour les échecs de validation Pydantic."""
    error_details = "\n" + "=" * 50
    error_details += f"\nDÉTAILS DES ERREURS DE VALIDATION : {model_name}"
    error_details += "\n" + "=" * 50
    for err in e.errors():
        # Reconstruit le chemin du champ (ex: activite -> type)
        loc = " -> ".join(str(item) for item in err["loc"])
        msg = err["msg"]
        type_err = err["type"]
        error_details += (
            f"\n❌ CHAMP : {loc}\n   MESSAGE : {msg}\n   TYPE : {type_err}\n"
        )
    error_details += "=" * 50
    return error_details

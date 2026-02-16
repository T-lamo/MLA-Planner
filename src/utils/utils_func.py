from typing import Any


def extract_field(data: Any, field: str, default: Any = None) -> Any:
    """Extrait un champ de manière sécurisée, que data soit un dict ou un objet."""
    if isinstance(data, dict):
        return data.get(field, default)
    return getattr(data, field, default)


__all__ = ["extract_field"]

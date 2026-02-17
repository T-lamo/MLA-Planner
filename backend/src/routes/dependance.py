from core.auth.auth_dependencies import get_current_active_user
from fastapi import Depends, HTTPException, status
from models.schema_db_model import Membre, Utilisateur


def get_current_membre(
    current_user: Utilisateur = Depends(get_current_active_user),
) -> Membre:
    """
    Récupère l'objet Membre associé à l'utilisateur authentifié.
    Lève une 403 si l'utilisateur n'est pas lié à un membre.
    """
    if not current_user.membre:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cet utilisateur n'est pas lié à un profil de membre.",
        )
    return current_user.membre

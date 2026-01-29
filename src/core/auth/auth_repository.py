from typing import Optional

from sqlmodel import Session, select

from models import Utilisateur


class AuthRepository:
    """Accès aux données pour l'authentification."""

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_username(self, username: str) -> Optional[Utilisateur]:
        """Récupère un utilisateur par son username."""
        statement = select(Utilisateur).where(Utilisateur.username == username)
        return self.db.exec(statement).first()

    def get_user_by_id(self, utilisateur_id: int) -> Optional[Utilisateur]:
        """Récupère un utilisateur par son ID."""
        return self.db.get(Utilisateur, utilisateur_id)

    def update_password(self, user: Utilisateur, hashed_password: str) -> Utilisateur:
        """Met à jour le mot de passe hashé d'un utilisateur."""
        user.password = hashed_password
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

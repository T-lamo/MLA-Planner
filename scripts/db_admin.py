import os
import sys

# On configure le path AVANT les imports locaux
# isort: skip
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from sqlmodel import Session, SQLModel

from conf.db.database import Database
from conf.db.seed.seed_service import SeedService


def recreate_db():
    engine = Database.get_engine()
    # Sécurité : on affiche le nom de la DB impactée
    print(f"⚠️  Destruction et recréation des tables : {engine.url.database}")
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    print("✅ Base de données remise à zéro.")


def seed_db():
    engine = Database.get_engine()
    with Session(engine) as session:
        print("🌱 Remplissage des données initiales...")
        SeedService(session).run()
        session.commit()
    print("✅ Seeding terminé.")


if __name__ == "__main__":
    args = sys.argv
    if "reset" in args:
        recreate_db()
    if "seed" in args:
        seed_db()

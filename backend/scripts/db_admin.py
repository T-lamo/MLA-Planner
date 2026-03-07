import os
import sys

# Configuration du path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from conf.db.database import Database
from conf.db.seed.seed_referential import SeedReferentials
from conf.db.seed.seed_service import SeedService
from sqlmodel import Session, SQLModel

def recreate_db():
    engine = Database.get_engine()
    url = str(engine.url)
    
    # --- SÉCURITÉ ANTI-CATASTROPHE ---
    if "render.com" in url or "clever-cloud" in url or os.getenv("ENV") == "production":
        print("❌ ERREUR CRITIQUE : Interdiction de reset la base de PRODUCTION.")
        print(f"URL détectée : {url}")
        sys.exit(1)

    print(f"⚠️  Destruction et recréation des tables : {engine.url.database}")
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    print("✅ Base de données remise à zéro.")

def seed_db():
    engine = Database.get_engine()
    print(f"🌱 [SEED] Remplissage de la base : {engine.url.database}...")

    # SeedService gère son propre begin/commit via `with self.db.begin()`
    with Session(engine) as session:
        try:
            SeedService(session).run()
            print("✅ SeedService terminé.")
        except Exception as e:
            session.rollback()
            print(f"❌ Erreur SeedService : {e}")
            sys.exit(1)

    # SeedReferentials (référentiels de base + membres de démo)
    with Session(engine) as session:
        try:
            SeedReferentials(session).run()
            session.commit()
            print("✅ SeedReferentials terminé.")
        except Exception as e:
            session.rollback()
            print(f"❌ Erreur SeedReferentials : {e}")
            sys.exit(1)

    print("✅ Seeding terminé avec succès.")


if __name__ == "__main__":
    args = sys.argv
    if "reset" in args:
        recreate_db()
    if "seed" in args:
        seed_db()
import os
import sys

# Configuration du path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from conf.db.database import Database
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
    # On utilise Session(engine) pour s'assurer d'être sur la bonne connexion
    with Session(engine) as session:
        try:
            print(f"🌱 [SEED] Remplissage de la base : {engine.url.database}...")
            SeedService(session).run()
            session.commit() # Important : commit explicite
            print("✅ Seeding terminé avec succès.")
        except Exception as e:
            session.rollback()
            print(f"❌ Erreur lors du seeding : {e}")
            sys.exit(1)

if __name__ == "__main__":
    args = sys.argv
    if "reset" in args:
        recreate_db()
    if "seed" in args:
        seed_db()
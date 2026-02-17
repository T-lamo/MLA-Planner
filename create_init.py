import os

# Chemin relatif vers le dossier src depuis le script
SRC_DIR = os.path.join(os.getcwd(), "src")

# Parcours tous les dossiers et sous-dossiers de src
for root, dirs, files in os.walk(SRC_DIR):
    init_file = os.path.join(root, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, "w", encoding="utf-8") as f:
            pass  # Crée un fichier vide
        # Affiche le chemin relatif pour suivi
        rel_path = os.path.relpath(init_file, os.getcwd())
        print(f"Créé : {rel_path}")

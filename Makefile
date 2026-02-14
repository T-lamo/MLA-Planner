# Variables
PYTHON = python3
APP_MODULE = src.main:app
# URL de la DB de test (utilisée pour les scripts admin et pytest)
DB_TEST_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/mla_test_db"
DB_ADMIN_SCRIPT = scripts/db_admin.py

.PHONY: test run install lint format clean precommit db-reset db-seed db-setup db-test-setup activate flake autoflake radon

# --- DEVELOPPEMENT ---

# Lancer l'application en mode développement (Uvicorn)
run:
	PYTHONPATH=src uvicorn $(APP_MODULE) --reload --host 0.0.0.0 --port 8000

# Installer les dépendances
install:
	pip install -r requirements.txt
	pip install flake8 autoflake radon

# --- QUALITE DE CODE ---

format:
	isort src --profile black
	black src
	autoflake --remove-all-unused-imports --remove-unused-variables -i -r src/

lint:
	isort --check-only --profile black src
	black --check src
	mypy src
	pylint src
	flake8 src

flake:
	flake8 src

autoflake:
	autoflake --in-place --remove-unused-variables --recursive src

radon:
	radon cc src -a
	radon mi src

precommit:
	pre-commit run --all-files

# --- TESTS & CI ---

# Setup complet de la DB de test (Reset + Seed spécifique test si besoin)
db-test-setup:
	@echo "🔧 Configuration de la base de données de TEST..."
	DATABASE_URL=$(DB_TEST_URL) ENV=testing $(PYTHON) $(DB_ADMIN_SCRIPT) reset
	@echo "✅ Base de test réinitialisée."

# Lancer les tests : Setup DB auto + Pytest
# On force ENV=testing pour que conftest.py utilise la bonne logique de protection
FILE ?= src/tests

# Lancer les tests : Setup DB auto + Pytest
# Utilisation de $(FILE) pour permettre le ciblage
test: 
	@echo "🚀 Lancement des tests sur : $(FILE)"
	DATABASE_URL=$(DB_TEST_URL) ENV=test pytest $(FILE) --cov=src --cov-report=term-missing -v
# --- BASE DE DONNEES (DEV) ---

# Supprime et recrée les tables sur la base de DEV
db-reset:
	$(PYTHON) $(DB_ADMIN_SCRIPT) reset

# Remplit la base de DEV (Seed)
db-seed:
	$(PYTHON) $(DB_ADMIN_SCRIPT) seed

# La totale pour le DEV
db-setup: db-reset db-seed

# --- UTILITAIRES ---

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -f .coverage coverage.xml .pytest_cache
	@echo "✨ Nettoyage terminé."

# Note: 'source' ne fonctionne pas directement dans un Makefile (processus fils)
# On affiche l'aide pour l'utilisateur
activate:
	@echo "Pour activer l'environnement virtuel, lancez : source .venv/bin/activate"
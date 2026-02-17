# Variables
PYTHON = python3
BACKEND_DIR = backend
APP_MODULE = src.main:app
# URL de la DB de test (utilisée pour les scripts admin et pytest)
DB_TEST_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/mla_test_db"
DB_ADMIN_SCRIPT = $(BACKEND_DIR)/scripts/db_admin.py

# Crucial pour que "import src" fonctionne toujours depuis la racine
export PYTHONPATH := $(BACKEND_DIR):$(BACKEND_DIR)/src

.PHONY: test test-debug run install lint format clean precommit db-reset db-seed db-setup db-test-setup activate flake autoflake radon

# --- DEVELOPPEMENT ---

# Lancer l'application en mode développement (Uvicorn)
run:
	uvicorn src.main:app --app-dir $(BACKEND_DIR) --reload --host 0.0.0.0 --port 8000
# Installer les dépendances
install:
	pip install -r $(BACKEND_DIR)/requirements.txt
	pip freeze > $(BACKEND_DIR)/requirements.txt
	@echo "✅ Dépendances figées dans $(BACKEND_DIR)/requirements.txt"
# --- QUALITE DE CODE ---

format:
	isort $(BACKEND_DIR)/src --profile black
	black $(BACKEND_DIR)/src
	autoflake --remove-all-unused-imports --remove-unused-variables -i -r $(BACKEND_DIR)/src
	flake8 $(BACKEND_DIR)/src

lint:
	isort --check-only --profile black $(BACKEND_DIR)/src
	black --check $(BACKEND_DIR)/src
	mypy $(BACKEND_DIR)/src
	pylint --rcfile=.pylintrc $(BACKEND_DIR)/src

flake:
	flake8 $(BACKEND_DIR)/src

autoflake:
	autoflake --in-place --remove-unused-variables --recursive $(BACKEND_DIR)/src

radon:
	radon cc $(BACKEND_DIR)/src -a
	radon mi $(BACKEND_DIR)/src

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
FILE ?= $(BACKEND_DIR)/src/tests

# Lancer les tests : Setup DB auto + Pytest
# Utilisation de $(FILE) pour permettre le ciblage
test: 
	@echo "🚀 Lancement des tests sur : $(FILE)"
	DATABASE_URL=$(DB_TEST_URL) ENV=test pytest --log-cli-level=INFO $(FILE) --cov=$(BACKEND_DIR)/src --cov-report=term-missing -v


test-debug:
	@echo "🐛 Debugging workflow : $(FILE)"
	DATABASE_URL=$(DB_TEST_URL) ENV=test pytest -s --log-cli-level=DEBUG $(FILE) -v
# --- BASE DE DONNEES (DEV) ---

# Supprime et recrée les tables sur la base de DEV
db-reset:
	DATABASE_URL=$(DB_TEST_URL) $(PYTHON) $(DB_ADMIN_SCRIPT) reset

# Remplit la base de DEV (Seed)
db-seed:
	$(PYTHON) $(DB_ADMIN_SCRIPT) seed

# La totale pour le DEV
db-setup: db-reset db-seed

# --- UTILITAIRES ---

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .coverage coverage.xml .pytest_cache
	@echo "✨ Nettoyage terminé."

# Note: 'source' ne fonctionne pas directement dans un Makefile (processus fils)
# On affiche l'aide pour l'utilisateur
activate:
	@echo "Pour activer l'environnement virtuel, lancez : source .venv/bin/activate"
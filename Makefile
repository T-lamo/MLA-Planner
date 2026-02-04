# Variables
PYTHON = python3
APP_MODULE = src.main:app
DB_TEST_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/mla_test_db"
DB_ADMIN_SCRIPT = scripts/db_admin.py

.PHONY: test run install lint format clean precommit db-reset db-seed db-setup activate flake autoflake radon

# --- DEVELOPPEMENT ---

# Lancer l'application en mode développement (Uvicorn)
run:
	PYTHONPATH=src uvicorn $(APP_MODULE) --reload --host 0.0.0.0 --port 8000

# Installer les dépendances
install:
	pip install -r requirements.txt
	pip install flake8 autoflake radon  # <-- ajout automatique

# --- QUALITE DE CODE ---

# Formater le code (répare les erreurs isort/black)
format:
	isort src --profile black
	black src
	autoflake --remove-all-unused-imports --remove-unused-variables -i -r src/

# Vérifier la qualité (sans modifier les fichiers)
lint:
	isort --check-only --profile black src
	black --check src
	mypy src
	pylint src
	flake8 src

# Exécuter flake8 uniquement
flake:
	flake8 src

# Nettoyer les imports inutilisés automatiquement
autoflake:
	autoflake --in-place --remove-unused-variables --recursive src

# Analyse de complexité (radon)
radon:
	radon cc src -a
	radon mi src

precommit:
	pre-commit run --all-files

# --- TESTS ---

# Lancer les tests sur la base de test dédiée
test:
	DATABASE_URL=$(DB_TEST_URL) ENV=test pytest --cov=src --cov-report=term-missing

# --- BASE DE DONNEES ---

# Supprime et recrée les tables
db-reset:
	$(PYTHON) $(DB_ADMIN_SCRIPT) reset

# Remplit la base (Seed)
db-seed:
	$(PYTHON) $(DB_ADMIN_SCRIPT) seed

# La totale : Reset + Seed
db-setup: db-reset db-seed

# --- UTILITAIRES ---

# Nettoyer les fichiers temporaires
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -f .coverage coverage.xml

env: 
	source .venv/bin/activate

# backend/Makefile
PYTHON = python3
APP_MODULE = src.main:app
DB_TEST_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/mla_test_db"
DB_ADMIN_SCRIPT = scripts/db_admin.py

# PYTHONPATH pour l'exécution interne
export PYTHONPATH := .:src

.PHONY: db-check db-status db-migrate db-upgrade db-downgrade test test-debug run install lint format clean precommit db-reset db-seed db-setup db-test-setup activate flake autoflake radon

# --- DEVELOPPEMENT ---
run:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

install:
	pip install -r requirements.txt
	pip freeze > requirements.txt
	@echo "✅ Dépendances figées dans requirements.txt"

# --- QUALITE DE CODE ---
format:
	isort src --profile black
	black src
	autoflake --remove-all-unused-imports --remove-unused-variables -i -r src
	flake8 src

lint:
	isort --check-only --profile black src
	black --check src
	mypy src
	pylint --rcfile=$(shell pwd)/.pylintrc src || pylint --rcfile=../.pylintrc src

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
db-test-setup:
	@echo "🔧 Configuration de la base de données de TEST..."
	DATABASE_URL=$(DB_TEST_URL) ENV=testing $(PYTHON) $(DB_ADMIN_SCRIPT) reset

FILE ?= tests  # On change le défaut pour qu'il soit relatif à src/
DB_TEST_URL ?= "postgresql+psycopg2://postgres:postgres@localhost:5432/mla_test_db"

test: 
	@echo "🚀 Lancement des tests sur : src/$(FILE)"
	@# On entre dans src pour que le conftest.py soit au bon niveau de collection
	cd src && \
	DATABASE_URL=$(DB_TEST_URL) \
	ENV=test \
	PYTHONPATH=. \
	pytest $(FILE) \
	--log-cli-level=INFO \
	--cov=. \
	--cov-report=term-missing -v

test-debug:
	@echo "🐛 Debugging workflow : src/$(FILE)"
	cd src && \
	DATABASE_URL=$(DB_TEST_URL) \
	ENV=test \
	PYTHONPATH=. \
	pytest -s --log-cli-level=DEBUG $(FILE) -v

# --- BASE DE DONNEES (DEV) ---
db-reset:
	DATABASE_URL=$(DB_TEST_URL) $(PYTHON) $(DB_ADMIN_SCRIPT) reset

db-seed:
	$(PYTHON) $(DB_ADMIN_SCRIPT) seed

db-setup: db-reset db-seed

# --- UTILITAIRES ---
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .coverage coverage.xml .pytest_cache
	@echo "✨ Nettoyage terminé."

activate:
	@echo "Pour activer l'environnement virtuel, lancez : source .venv/bin/activate"



db-migrate:
	@echo "🛠️  Génération d'une nouvelle migration..."
	alembic revision --autogenerate -m "$(MSG)"

# 2. Appliquer les migrations (Local ou Render selon ton .env)
db-upgrade:
	@echo "🚀 Application des migrations vers la base de données..."
	alembic upgrade head

# 3. Annuler la dernière migration
db-downgrade:
	@echo "⬅️  Retour à la version précédente..."
	alembic downgrade -1

# 4. Voir la version actuelle de la DB
db-status:
	@alembic current

# 5. COMMANDE DE DEBUG (Crucial pour ton problème actuel)
# Cette commande affiche les tables que SQLModel "voit" réellement avant de lancer Alembic.
db-check:
	@echo "🔍 Vérification des modèles détectés par SQLModel..."
	python3 -c "from sqlmodel import SQLModel; import src.models.schema_db_model as schema; [getattr(schema, n) for n in schema.__all__]; print(f'✅ Tables détectées ({len(SQLModel.metadata.tables)}):', list(SQLModel.metadata.tables.keys()))"
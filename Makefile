# Makefile à la racine du monorepo

.PHONY: ci-parallel dev-all dev-all-ui install-all format-front clean-all \
        dev-front lint-front typecheck-front test-front \
        dev-back install-back format-back lint-back flake-back autoflake-back radon-back precommit-back \
        test-back test-debug-back db-setup-back db-reset-back db-seed-back db-test-setup-back clean-back activate-back


# Lance le Backend et le Frontend en parallèle avec pnpm dlx
dev-all:
	@pnpm dlx concurrently -n "BACK,FRONT" -c "magenta,blue" \
		"$(MAKE) dev-back" \
		"$(MAKE) dev-front"

# Setup complet avec UI-Core
dev-all-ui:
	@pnpm dlx concurrently -n "BACK,FRONT,UI" -c "magenta,blue,green" \
		"$(MAKE) dev-back" \
		"$(MAKE) dev-front" \
		"$(MAKE) watch-ui"


# --- GLOBAL ---
install-all:
	cd backend && pip install -r requirements.txt
	cd frontend && pnpm install

ci-parallel:
	@echo "🚀 Running Front & Back checks in parallel..."
	$(MAKE) -j 2 run-back-ci run-front-ci

run-back-ci:
	$(MAKE) -C backend lint
	$(MAKE) -C backend test

run-front-ci:
	$(MAKE) -C frontend lint
	$(MAKE) -C frontend typecheck
	$(MAKE) -C frontend test

clean-all:
	$(MAKE) -C backend clean
	# Ajoutez ici le clean front si nécessaire (ex: rm -rf frontend/.nuxt)

# --- FRONTEND ---
dev-front:
	$(MAKE) -C frontend dev

format-front:
	$(MAKE) -C frontend format

lint-front:
	$(MAKE) -C frontend lint

typecheck-front:
	$(MAKE) -C frontend typecheck

test-front:
	$(MAKE) -C frontend test

# --- BACKEND (Toutes vos commandes d'origine) ---
dev-back:
	$(MAKE) -C backend run

install-back:
	$(MAKE) -C backend install

format-back:
	$(MAKE) -C backend format

lint-back:
	$(MAKE) -C backend lint

flake-back:
	$(MAKE) -C backend flake

autoflake-back:
	$(MAKE) -C backend autoflake

radon-back:
	$(MAKE) -C backend radon

precommit-back:
	$(MAKE) -C backend precommit

test-back:
	$(MAKE) -C backend test FILE=$(FILE)

test-debug-back:
	$(MAKE) -C backend test-debug FILE=$(FILE)

db-setup-back:
	$(MAKE) -C backend db-setup

db-reset-back:
	$(MAKE) -C backend db-reset

db-seed-back:
	$(MAKE) -C backend db-seed

db-test-setup-back:
	$(MAKE) -C backend db-test-setup

clean-back:
	$(MAKE) -C backend clean

activate-back:
	$(MAKE) -C backend activate



# --- UI-CORE (Web Components) ---
# Compiler la lib UI avant le front
build-ui:
	$(MAKE) -C packages/ui-core build

# Lancer le watch en arrière-plan pendant le dev Nuxt
watch-ui:
	$(MAKE) -C packages/ui-core watch

ui-clean:
	$(MAKE) -C packages/ui-core clean

# --- FRONTEND (Modifié pour dépendre de l'UI) ---
# On s'assure que l'UI est compilée avant de build Nuxt
build-front: build-ui
	$(MAKE) -C frontend build

# --- CI PIPELINE UPDATE ---
# Cette commande sera appelée par GitHub Actions
run-ui-ci:
	$(MAKE) -C packages/ui-core build
	

# Nouvelles commandes pour Alembic
db-migrate-back:
	$(MAKE) -C backend db-migrate MSG="$(MSG)"

db-upgrade-back:
	$(MAKE) -C backend db-upgrade

db-downgrade-back:
	$(MAKE) -C backend db-downgrade



git-change-front: 
	git diff --cached -- "*.ts" "*.vue" "*.css" "package.json" > debug_change.patch

git-change-back: 
	git diff --cached -- "*.py" > debug_change.patch



PYTHON = python3
SCRIPT = merge_models.py
SRC_DIR = ./app/models
OUT_FILE = ./app/models_all.py
EXCLUDE = __init__.py base_model.py
debug-merge:
	@echo "Commande prévue :"
	@echo "$(PYTHON) $(SCRIPT) --dir $(SRC_DIR) --out $(OUT_FILE) --exclude $(EXCLUDE)"

run-merge:
	$(PYTHON) $(SCRIPT) --dir $(SRC_DIR) --out $(OUT_FILE) --exclude $(EXCLUDE)
# Makefile à la racine du monorepo

.PHONY: ci-parallel install-all clean-all \
        dev-front lint-front typecheck-front test-front \
        dev-back install-back format-back lint-back flake-back autoflake-back radon-back precommit-back \
        test-back test-debug-back db-setup-back db-reset-back db-seed-back db-test-setup-back clean-back activate-back

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


# Nouvelles commandes pour Alembic
db-migrate-back:
	$(MAKE) -C backend db-migrate MSG="$(MSG)"

db-upgrade-back:
	$(MAKE) -C backend db-upgrade

db-downgrade-back:
	$(MAKE) -C backend db-downgrade
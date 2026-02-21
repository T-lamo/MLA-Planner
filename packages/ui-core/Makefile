# packages/ui-core/Makefile

.PHONY: install build watch link-pkg clean

# Installation des dépendances spécifiques à Lit et TypeScript
install:
	pnpm install

# Compilation des TypeScript en JavaScript utilisable par Nuxt (dist/)
build:
	pnpm build

# Mode développement : re-compile automatiquement à chaque changement
watch:
	pnpm dev

# Nettoyage des fichiers compilés
clean:
	rm -rf dist

# --- PROCESS WEB COMPONENTS ---
# 1. On code dans src/*.ts
# 2. 'make build' génère les fichiers dans dist/
# 3. Nuxt consomme '@shared/ui-core' via le workspace pnpm
# 4. En cas de changement, il faut souvent rebuild pour que Nuxt voit les types à jour
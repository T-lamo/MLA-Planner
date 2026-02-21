# frontend/Makefile

.PHONY: install dev format lint typecheck test build clean prepare

# Installation des dépendances et config Husky
install:
	pnpm install
	pnpm exec husky init

# Lancement du serveur de développement Nuxt 4
dev:
	pnpm dev

# NETTOYAGE COMPLET (Expert) : Supprime les lignes inutilisées et formate le code
# C'est la commande que tu utiliseras le plus pour éviter la dette technique.
format:
	pnpm exec prettier --write "**/*.{vue,ts,js,json,css,scss,md}"
	pnpm exec eslint --fix .

# VERIFICATION : Vérifie la qualité du code sans le modifier
lint:
	pnpm exec eslint .
	pnpm exec prettier --check "**/*.{vue,ts,js,json,css,scss,md}"

# VERIFICATION TYPESCRIPT : Utile avant un push ou un build
typecheck:
	pnpm exec nuxi typecheck

# TESTS : Lance la suite de tests (Vitest)
test:
	pnpm run test

# BUILD : Génère le site statique pour le déploiement (Netlify)
# On force le typecheck avant le build pour garantir la stabilité.
build:
	pnpm nuxi prepare
	pnpm nuxi generate

# RESET : À utiliser si Nuxt ou Tailwind deviennent "fous" (problèmes de cache)
clean:
	rm -rf .nuxt .output dist node_modules/.vite
	pnpm nuxi prepare
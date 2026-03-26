# Guide de contribution — MLA Planner

Ce guide s'adresse aux développeurs qui rejoignent le projet. Lisez-le entièrement avant d'ouvrir votre première PR.

---

## Option A — Lancer avec Docker (recommandé pour démarrer vite)

Seul prérequis : **[Docker Desktop](https://www.docker.com/products/docker-desktop/)**.

```bash
git clone https://github.com/T-lamo/MLA-Planner.git
cd MLA-Planner/mla-app
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API + Swagger | http://localhost:8000/docs |

Les données de démonstration (campus, ministères, membres, plannings) sont créées automatiquement.

> Docker n'est pas recommandé pour le développement actif car chaque modification du code source nécessite un rebuild. Utilisez l'option B pour coder.

---

## Option B — Installation locale (développement actif)

### Prérequis

| Outil | Version minimale | Installation |
|---|---|---|
| Python | 3.12 | [python.org](https://www.python.org/downloads/) |
| Node.js | 22 LTS | [nodejs.org](https://nodejs.org/) |
| pnpm | 9+ | `npm install -g pnpm` |
| PostgreSQL | 15+ | [postgresql.org](https://www.postgresql.org/download/) |
| Make | — | Natif Linux/macOS · `choco install make` Windows |

### Installation

```bash
# 1. Cloner le dépôt
git clone https://github.com/T-lamo/MLA-Planner.git
cd MLA-Planner/mla-app

# 2. Installer toutes les dépendances (backend + frontend)
make install-all

# 3. Configurer les variables d'environnement backend
cp .env.example .env
# Ajuster DATABASE_URL pour pointer vers votre PostgreSQL local

# 4. Initialiser la base de données (reset + migrations + seed)
make db-setup-back

# 5. Lancer en développement
make dev-all
```

- **Backend** : `http://localhost:8000` — Swagger UI : `http://localhost:8000/docs`
- **Frontend** : `http://localhost:3000`

---

## Comptes de test

Tous les comptes non-superadmin ont le mot de passe `plan123!`.

| Username | Mot de passe | Rôle | Campus | Ministère |
|---|---|---|---|---|
| `superadmin` | `plan123!` | Super Admin | — | — |
| `amos` | `plan123!` | Admin | Paris · Toulouse | Louange et Adoration |
| `jean` | `plan123!` | Responsable MLA | Paris | Technique |
| `awa` | `plan123!` | Membre MLA | Paris | Accueil · Jeunesse |

---

## Pipeline obligatoire

**Ces quatre commandes doivent toutes passer avant chaque commit.** Le hook Husky les vérifie automatiquement, mais lancez-les en local pour corriger avant :

```bash
make format-back && make lint-back && make test-back && make format-front
```

| Commande | Ce qu'elle fait |
|---|---|
| `make format-back` | isort + black + autoflake + flake8 |
| `make lint-back` | isort check + black check + mypy strict + pylint (note : 10.00/10 obligatoire) |
| `make test-back` | pytest avec coverage |
| `make format-front` | Prettier + ESLint auto-fix |

Pour lancer un seul fichier de test :
```bash
make test-back FILE=tests/test_chant.py
```

---

## Conventions

### Branches
```
feature/<us-id>-<description-courte>   # Nouvelle fonctionnalité
fix/<description>                       # Correctif
refactor/<description>                  # Refactoring sans nouvelle fonctionnalité
```

### Commits (Conventional Commits)
```
feat(scope): description courte
fix(scope): description courte
refactor(scope): description courte
test(scope): description courte
docs(scope): description courte
```

Exemples :
```
feat(planning): génération de série hebdomadaire US-98
fix(songbook): rechargement réactif des chants au changement de campus
```

### Python
- mypy strict — zéro `# type: ignore`
- `TypedDict` pour tous les dicts de config/seed
- max 15 variables locales par méthode (pylint R0914)
- max 50 statements par méthode (pylint R0915)
- max 5 arguments positionnels (pylint R0917) — au-delà, utiliser `*` pour keyword-only
- Lignes max 88 caractères (flake8 E501)
- Toute méthode de seed > 2 entités → sous-méthodes `_seed_<nom>()`

### TypeScript
- Strict mode — pas de `as any`
- Les IDs backend sont des `str` (UUID v4), jamais `number`
- Pas d'import direct hors `lucide-vue-next` pour les icônes

### CSS / Tailwind
- TailwindCSS **v4 uniquement** — ne pas utiliser de classes v3 (`ring`, `shadow-md`, `bg-opacity-*`)
- Variables via `var(--color-*)` ou syntaxe v4 `text-(--color-primary-700)`
- `@reference "../assets/css/main.css"` dans chaque `<style scoped>` qui utilise `@apply`
- Pas de `style="..."` sauf pour les valeurs dynamiques JS

---

## Architecture backend (résumé)

```
routes/      → Endpoints uniquement — injectent Session via Depends(get_db)
services/    → Toute la logique métier
repositories/→ Requêtes SQLModel/SQLAlchemy
models/      → SQLModel DB + Pydantic schemas
core/        → Auth, exceptions, config
```

- `BaseService` fournit `get_one`, `create`, `update`, `hard_delete` — ne pas les réimplémenter
- `AppException(ErrorRegistry.XXX)` — jamais `HTTPException` directement dans un service
- Seed idempotent via `_get_or_create()` — jamais `db.add()` seul en seed

## Architecture frontend (résumé)

```
layers/base/      → Layout, TopBar, sidebar, pages admin, stores UI
layers/auth/      → Login, middleware auth, store auth
layers/planning/  → Calendrier, formulaires, templates, stores planning
layers/songbook/  → Répertoire chants, éditeur ChordPro
packages/ui-core/ → Web Components partagés (préfixe ui-)
```

- Stores Pinia dans `layers/*/app/stores/useXxxStore.ts`
- Appels API via `useApi()` composable — jamais `$fetch` direct
- Un store ne doit pas appeler un autre store dans son état initial — utiliser `watch` dans le composant parent

---

## Pièges connus

| Piège | Cause | Fix |
|---|---|---|
| 404 sur `GET /ministeres/{id}/full` | UUID hardcodé | Utiliser `selectedCampusId` depuis `useUiStore` |
| mypy `object` incompatible | `Dict[str, object]` sans TypedDict | Ajouter un `TypedDict` dans `data.py` |
| Tailwind class sans effet | Classe v3 dans un projet v4 | Vérifier la doc Tailwind v4 |
| `CampusMinistereLink` manquant | Ministère non lié à tous les campus | Boucler sur tous les campus dans `_seed_ministeres` |
| Pinia store côté serveur | Import direct sans plugin | `useXxxStore()` dans `setup()` ou `onMounted` |
| pylint R0914/R0915 | Tout le seed dans une seule méthode | Une sous-méthode `_seed_pX_<nom>()` par entité principale |
| Réponse vide sur `previewSeries` | `unwrap()` sur endpoint non enveloppé | Utiliser `apiRequest()` directement et déstructurer `{ data }` |
| Vue compile error `@click` multi-ligne | Tokenizer Vue 3.5 | Extraire en méthode nommée dans `<script setup>` |
| Rôle `"Admin"` vs `"ADMIN"` | `RoleName.ADMIN.name` retourne le nom enum | Utiliser les noms enum (`"ADMIN"`, `"SUPER_ADMIN"`) dans `RoleChecker` |

---

## Commandes Makefile complètes

```bash
# Développement
make install-all          # Installe backend + frontend
make dev-all              # Lance backend + frontend en parallèle
make dev-back             # Lance uniquement FastAPI (hot-reload)
make dev-front            # Lance uniquement Nuxt

# Base de données
make db-setup-back        # Reset + migrations + seed (source de vérité)
make db-reset-back        # Reset uniquement
make db-seed-back         # Seed uniquement
make db-upgrade-back      # Applique les migrations Alembic
make db-downgrade-back    # Reverte la dernière migration
make db-migrate-back MSG="description"  # Génère une nouvelle migration

# Qualité Backend
make format-back          # Formatte (isort + black + autoflake + flake8)
make lint-back            # Vérifie (isort + black + mypy + pylint)
make test-back            # Tests (pytest + coverage)
make test-back FILE=tests/test_foo.py  # Test d'un seul fichier

# Qualité Frontend
make format-front         # Prettier + ESLint fix
make lint-front           # Lint uniquement
make typecheck-front      # tsc --noEmit

# UI-Core
make build-ui             # Build les Web Components
make watch-ui             # Mode watch pour le développement
```

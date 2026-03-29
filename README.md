# MLA Planner

[![CI](https://github.com/T-lamo/MLA-Planner/actions/workflows/ci.yml/badge.svg)](https://github.com/T-lamo/MLA-Planner/actions)
[![Coverage](https://codecov.io/gh/T-lamo/MLA-Planner/branch/develop/graph/badge.svg)](https://codecov.io/gh/T-lamo/MLA-Planner)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128-009688)
![Nuxt](https://img.shields.io/badge/Nuxt-4.3-00DC82)
![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-4.2-38BDF8)

> Application web SaaS multi-tenant de gestion et planification des services pour le projet **MLA / ICC**. Conçue pour des équipes de ministères (Louange, Technique, Accueil, Jeunesse…) qui ont besoin d'organiser leurs plannings, leurs équipes et leur répertoire de chants.

---

## Lancer avec Docker

> Seul prérequis : **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** (Mac / Windows / Linux).
> Aucune installation de Python, Node ou PostgreSQL nécessaire.

### Démarrage en 3 commandes

```bash
git clone https://github.com/T-lamo/MLA-Planner.git
cd MLA-Planner/mla-app
docker compose up --build
```

> Le premier `--build` télécharge les images et compile le frontend (~3–5 min selon votre connexion).
> Les démarrages suivants (`docker compose up`) sont instantanés grâce au cache Docker.

### Accès aux services

| Service | URL | Description |
|---|---|---|
| **Application** | http://localhost:3000 | Interface utilisateur complète |
| **API Swagger** | http://localhost:8000/docs | Documentation interactive des endpoints |
| **Health check** | http://localhost:8000/health | Statut de l'API (`{"status": "ok"}`) |
| **Base de données** | `localhost:5432` | PostgreSQL — user: `mla` · pass: `mla` · db: `mla_db` |

### Comptes de démonstration

Les comptes sont créés automatiquement au premier démarrage (seed idempotent).

| Identifiant | Mot de passe | Rôle | Ministère |
|---|---|---|---|
| `superadmin` | `plan123!` | Super Admin | — |
| `amos` | `plan123!` | Admin | Louange |
| `jean` | `plan123!` | Responsable | Technique |
| `awa` | `plan123!` | Membre | Accueil |

### Commandes utiles

```bash
# Démarrer en arrière-plan
docker compose up --build -d

# Voir les logs en temps réel
docker compose logs -f

# Logs d'un seul service
docker compose logs -f backend
docker compose logs -f frontend

# Arrêter les conteneurs (données conservées)
docker compose down

# Arrêter ET supprimer la base de données (repartir à zéro)
docker compose down -v

# Rebuilder uniquement un service après modification du code
docker compose up --build backend
docker compose up --build frontend

# Ouvrir un shell dans le conteneur backend
docker compose exec backend sh

# Lancer les migrations manuellement
docker compose exec backend alembic upgrade head

# Relancer le seed de démo
docker compose exec backend python scripts/db_admin.py seed
```

### Dépannage

| Problème | Cause probable | Solution |
|---|---|---|
| Port 3000 ou 8000 déjà utilisé | Autre service actif sur ce port | `docker compose down` puis libérer le port |
| `frontend` ne démarre pas | Le backend n'est pas encore prêt | Attendre ~60s, c'est normal (migrations + seed) |
| Données incohérentes | Volume DB corrompu | `docker compose down -v && docker compose up --build` |
| Build échoue sur `pnpm install` | Lockfile désynchronisé | Supprimer l'image : `docker compose build --no-cache frontend` |
| `connection refused` sur l'API | Backend encore en cours de démarrage | Vérifier `docker compose logs backend` et attendre |

---

## Ce que fait l'application

**MLA Planner** centralise la vie opérationnelle d'une communauté multi-campus. Elle permet aux responsables de créer des plannings d'activités, d'y affecter les membres selon leurs rôles et compétences, et de gérer les indisponibilités en amont.

Les membres reçoivent leurs propositions d'affectation, confirment ou refusent leur participation, et consultent leur agenda personnel. Les responsables suivent en temps réel le remplissage de chaque créneau.

Un module **Répertoire de chants** partagé permet à toutes les équipes de consulter les partitions ChordPro, de les transposer à la volée et d'organiser leur catalogue par catégorie et artiste.

---

## Stack technique

| Couche | Technologies |
|---|---|
| **Backend** | Python 3.12 · FastAPI 0.128 · SQLModel 0.0.31 · SQLAlchemy 2.0 · Alembic 1.18 |
| **Base de données** | PostgreSQL 16 · psycopg2 2.9 |
| **Auth** | JWT HS256 + JTI blacklist · PyJWT 2.10 |
| **Frontend** | Nuxt 4.3 · Vue 3.5 · TypeScript 5.9 · Pinia 3 · TailwindCSS 4.2 |
| **Calendrier** | FullCalendar 6.1 (daygrid, timegrid, list) |
| **UI partagée** | Web Components (`ui-*`) dans `packages/ui-core/` |
| **Qualité** | mypy strict · pylint · ruff · black · isort · pytest 9 · Vitest 4 |
| **CI** | GitHub Actions · Husky pre-commit |

---

## Fonctionnalités clés

- **Plannings multi-ministères** : création, publication, workflow (Brouillon → Publié → Terminé)
- **Affectations par rôle** : proposition → confirmation → présence, avec détection des indisponibilités
- **Générateur de séries** : créer N plannings récurrents (hebdo/mensuel) depuis un template
- **Bibliothèque de templates** : sauvegarder, réutiliser et partager des structures de planning
- **Visibilité des templates** : Privé / Ministère / Campus
- **Répertoire de chants** : ChordPro, transposition, YouTube, filtres par catégorie et artiste
- **RBAC** : 4 niveaux de rôles — Super Admin · Admin · Responsable MLA · Membre MLA
- **Multi-tenant** : isolation complète par campus et ministère
- **Agenda personnel** : chaque membre consulte ses affectations à venir

---

## Architecture en un coup d'œil

```
mla-app/
├── backend/              # FastAPI — Python 3.12
│   ├── src/
│   │   ├── routes/       # Endpoints (thin controllers)
│   │   ├── services/     # Logique métier
│   │   ├── models/       # SQLModel + Pydantic schemas
│   │   ├── repositories/ # Requêtes DB
│   │   └── core/         # Auth, exceptions, config
│   └── alembic/          # Migrations PostgreSQL
├── frontend/             # Nuxt 4 — Vue 3 + TypeScript
│   └── layers/
│       ├── base/         # Layout, sidebar, admin
│       ├── auth/         # Login, middleware JWT
│       ├── planning/     # Calendrier, templates, séries
│       └── songbook/     # Répertoire de chants
└── packages/
    └── ui-core/          # Web Components partagés (préfixe ui-)
```

---

## Démarrage rapide

```bash
# 1. Dépendances
make install-all

# 2. Base de données (reset + migrations + seed)
make db-setup-back

# 3. Lancer l'application complète
make dev-all
```

Backend disponible sur `http://localhost:8000` · Frontend sur `http://localhost:3000`

**Comptes de test** (mot de passe universel : `plan123!`) :

| Username | Rôle | Ministère |
|---|---|---|
| `superadmin` | Super Admin | — |
| `amos` | Admin | Louange et Adoration |
| `jean` | Responsable MLA | Technique |
| `awa` | Membre MLA | Accueil · Jeunesse |

---

## Documentation

| Fichier | Audience | Contenu |
|---|---|---|
| [CONTRIBUTING.md](CONTRIBUTING.md) | Développeurs | Installation, pipeline CI, conventions, pièges |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Développeurs | Couches, patterns, décisions techniques |
| [API.md](API.md) | Intégrateurs | Endpoints, auth, format des erreurs |
| [SECURITY.md](SECURITY.md) | Auditeurs | Auth JWT, RBAC, isolation des données |
| [CLAUDE.md](CLAUDE.md) | IA / Contributeurs | Règles absolues pour les contributions assistées |

---

## Licence

Projet privé — MLA / ICC. Tous droits réservés.

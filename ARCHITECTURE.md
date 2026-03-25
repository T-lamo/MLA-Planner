# Architecture — MLA Planner

Ce document décrit les décisions d'architecture et les patterns utilisés dans le projet. Il s'adresse aux développeurs qui reprennent le code ou qui veulent comprendre les choix structurels.

---

## Vue d'ensemble du monorepo

```
mla-app/
├── backend/                    # API FastAPI — Python 3.12
│   ├── src/
│   │   ├── routes/             # Routers FastAPI (controllers)
│   │   ├── services/           # Logique métier
│   │   ├── repositories/       # Accès base de données
│   │   ├── models/             # SQLModel (DB) + Pydantic (DTO)
│   │   ├── core/
│   │   │   ├── auth/           # JWT, RoleChecker, get_current_active_user
│   │   │   ├── exceptions/     # AppException, handlers
│   │   │   └── message.py      # ErrorRegistry (source de vérité des erreurs)
│   │   ├── conf/
│   │   │   └── db/seed/        # Données de test idempotentes
│   │   └── mla_enum/           # Enums partagés (RoleName, etc.)
│   ├── alembic/versions/       # Migrations PostgreSQL
│   └── .pylintrc               # Config pylint (max 88 chars, R0914, R0915...)
│
├── frontend/                   # App Nuxt 4 — Vue 3 + TypeScript
│   ├── layers/
│   │   ├── base/               # Fondations : layout, sidebar, admin, stores UI
│   │   ├── auth/               # Login, middleware, store auth, cookies JWT
│   │   ├── planning/           # Calendrier, plannings, templates, séries
│   │   └── songbook/           # Répertoire de chants ChordPro
│   ├── assets/css/main.css     # Variables CSS Tailwind v4
│   └── nuxt.config.ts          # Configuration des layers
│
└── packages/
    └── ui-core/                # Web Components partagés (préfixe ui-)
```

---

## Backend

### Pattern Couches

```
HTTP Request
     │
  Router (routes/)          ← Valide les paramètres, injecte Session via Depends
     │
  Service (services/)       ← Toute la logique métier
     │
  Repository (repositories/)← Requêtes SQLModel/SQLAlchemy
     │
  PostgreSQL
```

**Règle absolue** : aucune logique métier dans les routers. Aucun accès DB direct dans les services (passer par le repo ou la session injectée).

### BaseService

`BaseService` fournit les opérations CRUD génériques :
- `get_one(id)` → lève `AppException(ErrorRegistry.CORE_001)` si absent
- `create(data)` → persiste et retourne le modèle
- `update(id, data)` → met à jour les champs non-null
- `hard_delete(id)` → supprime définitivement

Ne jamais réimplémenter ces méthodes dans les services spécialisés — les surcharger uniquement si le comportement doit changer.

### Gestion des erreurs

```python
# Correct
raise AppException(ErrorRegistry.PLAN_001)

# Interdit dans un service
raise HTTPException(status_code=400, detail="...")
```

`ErrorRegistry` dans `core/message.py` est la **source de vérité unique** pour tous les codes d'erreur. Format de réponse unifié :

```json
{
  "error": {
    "code": "PLAN_001",
    "message": "Ce planning ne peut plus être modifié.",
    "status": 409
  }
}
```

Le frontend lit `error.error.code` pour les traitements spécifiques.

### Modèles SQLModel

Deux types de modèles cohabitent :
- **DB models** dans `models/schema_db_model.py` : classes avec `table=True`, relations SQLAlchemy
- **Pydantic DTOs** dans `models/<domaine>_model.py` : schemas de lecture/écriture

Convention de nommage des tables : `t_<nom>` (ex : `t_planningservice`, `t_membre`).

Les IDs sont des `str` (UUID v4 générés par la DB), jamais des entiers.

### Auth JWT

```
Login → JWT (HS256) avec payload : sub, jti (UUID v4), exp, roles
     ↓
Chaque requête → vérification signature → lookup JTI dans t_revoked_tokens
     ↓
RoleChecker(["ADMIN", "RESPONSABLE_MLA"]) → extrait libelle.name des affectations
```

Le `RoleChecker` utilise `.name` des valeurs de `RoleName` enum (`"ADMIN"`, `"SUPER_ADMIN"`, etc.) — ne pas confondre avec `.value` (`"Admin"`, `"Super Admin"`).

Superadmin bypass : si `RoleName.SUPER_ADMIN.name` est dans les rôles de l'user, toutes les vérifications de rôle passent automatiquement.

---

## Frontend

### Système de Layers Nuxt 4

Les layers sont des **modules Nuxt autonomes** qui s'étendent les uns les autres. Chaque layer a sa propre arborescence `app/` :

```
layers/<nom>/
└── app/
    ├── pages/          # Routes automatiques
    ├── components/     # Composants auto-importés
    ├── composables/    # Composables auto-importés
    ├── stores/         # Stores Pinia
    ├── repositories/   # Accès API
    └── types/          # Types TypeScript
```

Ordre des layers dans `nuxt.config.ts` : `base → auth → planning → songbook`. Un layer peut utiliser les composants et composables des layers précédents.

### Stores Pinia

Pattern uniforme :

```typescript
// layers/planning/app/stores/usePlanningStore.ts
export const usePlanningStore = defineStore('planning', () => {
  // state
  const plannings = ref<PlanningRead[]>([])

  // computed
  const draftCount = computed(() => plannings.value.filter(p => p.statut === 'BROUILLON').length)

  // actions
  async function load(campusId: string) { ... }

  return { plannings, draftCount, load }
})
```

**Règle** : un store ne doit pas appeler un autre store dans son état initial. Utiliser `watch` dans le composant parent pour réagir aux changements de store.

### Appels API

Tous les appels passent par `useApi()` (composable wrappant `$fetch`) via les repositories :

```typescript
// layers/planning/app/repositories/PlanningRepository.ts
export class PlanningRepository extends BaseRepository {
  async list(campusId: string): Promise<PlanningRead[]> {
    const { data } = await this.apiRequest<PlanningRead[]>(`/planning/by-campus/${campusId}`)
    return data
  }
}
```

`apiRequest()` retourne `{ data: T }` (enveloppe). Certains endpoints retournent la donnée directement (sans enveloppe) — utiliser `apiRequest()` et déstructurer manuellement dans ce cas.

### Middleware Auth

Deux middlewares globaux, exécutés dans cet ordre :

1. **`01.auth.global.ts`** — Vérifie l'expiration du token, hydrate le store auth au F5, redirige vers `/login` si non authentifié
2. **`02.admin.global.ts`** — Protège les routes `/admin/*`, vérifie `hasAdminAccess`

Ne jamais changer les préfixes `01.`/`02.` sans vérifier l'ordre d'exécution Nuxt.

### Gestion des rôles côté frontend

```typescript
// useAuthStore.ts
const isSuperAdmin  = computed(() => user.value?.roles?.includes('Super Admin') ?? false)
const isAdmin       = computed(() => user.value?.roles?.includes('Admin') ?? false)
const isResponsable = computed(() => user.value?.roles?.includes('Responsable MLA') ?? false)
const hasAdminAccess   = computed(() => isSuperAdmin.value || isAdmin.value)
const canManageChants  = computed(() => isSuperAdmin.value || isAdmin.value || isResponsable.value)
```

---

## Multi-tenancy

L'isolation des données repose sur deux dimensions :

- **Campus** : chaque membre appartient à un ou plusieurs campus (`MembreCampusLink`)
- **Ministère** : chaque membre a accès à un ou plusieurs ministères (`MembreMinistereLink`)

La table de liaison `CampusMinistereLink` doit exister pour chaque couple (campus, ministère). Oubli fréquent dans le seed → toujours boucler sur tous les campus lors de la création d'un ministère.

Toute requête planning doit être filtrée par `campus_id` **ou** `ministere_id` de l'utilisateur courant. Exception : le module Songbook est un répertoire commun à tous les campus — pas de filtre campus_id.

---

## Statuts et workflow

### Planning
```
BROUILLON → PUBLIE → TERMINE
    └──────→ ANNULE (depuis n'importe quel statut)
```

### Affectation
```
PROPOSE → CONFIRME → PRESENT
    └───→ REFUSE
```

Les transitions invalides lèvent `AppException(ErrorRegistry.WKFL_001)`.

---

## Base de données

### Migrations Alembic

```bash
# Générer une migration
make db-migrate-back MSG="add_visibilite_to_planning_template"

# Appliquer
make db-upgrade-back

# Revenir en arrière
make db-downgrade-back
```

Toujours relire le fichier de migration généré avant de l'appliquer — Alembic peut rater des cas (renommage de colonne, changement de type).

### Seed idempotent

Le seed utilise `_get_or_create()` pour être rejouable sans créer de doublons :

```python
def _get_or_create(db, model, defaults=None, **kwargs):
    obj = db.exec(select(model).filter_by(**kwargs)).first()
    if obj is None:
        obj = model(**(defaults or {}), **kwargs)
        db.add(obj)
    return obj
```

Données de test dans `backend/src/conf/db/seed/data.py` — source de vérité unique, avec `TypedDict` pour chaque structure.

---

## Décisions d'architecture

| Décision | Raison |
|---|---|
| SQLModel plutôt qu'SQLAlchemy seul | Validation Pydantic + types Python directement dans le modèle DB |
| Nuxt 4 layers plutôt qu'un monolithe | Isolation des modules, possibilité de désactiver un layer sans impacter les autres |
| JWT + JTI blacklist | Révocation de token sans état serveur global, requis pour le logout immédiat |
| Pinia stores par layer | Évite les couplages croisés et facilite le tree-shaking |
| `ErrorRegistry` centralisé | Un seul endroit pour modifier les messages d'erreur, tests plus simples |
| TailwindCSS v4 CSS-first | Variables CSS natives, moins de configuration JS, meilleure performance |
| Web Components pour `ui-core` | Réutilisables hors Nuxt si nécessaire, isolation des styles garantie |

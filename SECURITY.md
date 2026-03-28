# Sécurité — MLA Planner

Ce document décrit les mécanismes de sécurité en place et les points à renforcer avant la mise en production. Il s'adresse aux auditeurs de sécurité et aux recruteurs qui souhaitent évaluer la maturité sécurité du projet.

---

## Authentification

### JWT HS256 + JTI Blacklist

```
Login → JWT signé HS256
         ├── sub      : user_id (UUID v4)
         ├── jti      : UUID v4 unique par token
         ├── exp      : expiration (configurable, défaut 30 min)
         └── roles    : liste des libellés de rôles

Chaque requête :
  1. Vérification de la signature JWT
  2. Lookup du JTI dans t_revoked_tokens (blacklist DB)
  3. Si révoqué → 401 immédiat
  4. Vérification expiration
  5. Chargement de l'utilisateur actif
```

**Pourquoi JTI + blacklist ?**
Le logout standard JWT ne révoque pas le token avant son expiration naturelle. La blacklist JTI permet une révocation immédiate sans état serveur global distribué.

### Token sans JTI

Tout token ne contenant pas de champ `jti` est rejeté avec HTTP 401 — pas de fallback silencieux.

### Refresh Token

- Distinct du token d'accès (JTI différent, durée de vie plus longue)
- Révoqué à la connexion suivante (`POST /auth/refresh` invalide l'ancien refresh token)
- Stocké côté client dans un cookie `HttpOnly`

---

## Cookies

| Cookie | Valeur | Protection |
|---|---|---|
| `auth_token` | JWT d'accès | `HttpOnly`, `sameSite: strict`, `secure: true` |
| `auth_expires_at` | Date d'expiration | `sameSite: strict`, `secure: true` |
| `auth_user` | Données user sérialisées | `sameSite: strict`, `secure: true` |

- **`HttpOnly`** : le JavaScript ne peut pas lire le token d'accès — protection XSS
- **`sameSite: strict`** : protection CSRF
- **`secure: true`** : transmission HTTPS uniquement en production
- **Jamais `localStorage`** pour les tokens JWT

---

## RBAC — Contrôle d'accès basé sur les rôles

### Hiérarchie

```
Super Admin
    └── Admin
            └── Responsable MLA
                        └── Membre MLA
```

| Rôle | Valeur JWT | Permissions |
|---|---|---|
| **Super Admin** | `Super Admin` | Accès total + configuration des campus |
| **Admin** | `Admin` | Gestion complète des plannings + membres sur ses campus |
| **Responsable MLA** | `Responsable MLA` | Création/gestion plannings, templates, affectations |
| **Membre MLA** | `Membre MLA` | Lecture plannings, gestion de ses propres affectations |

### Implémentation backend

Quatre guards injectables via `Depends()` :

```python
# RoleChecker — rôle actif temporellement valide
Depends(RoleChecker(["ADMIN", "RESPONSABLE_MLA"]))

# ScopedRoleChecker — rôle + vérification du scope ministère
Depends(ScopedRoleChecker(["ADMIN", "RESPONSABLE_MLA"]))
# → l'affectation doit avoir un contexte couvrant le ministere_id de la requête

# CasbinGuard — moteur RBAC with domains (Casbin)
Depends(CasbinGuard("planning", "write", fallback_roles=["ADMIN"]))
# → sub=user.id, dom=ministere_id, obj="planning", act="write"

# CapabilityChecker — permission granulaire codée
Depends(CapabilityChecker(["MEMBRE_READ"]))
# → vérifie le champ 'capabilities' du JWT, fallback sur les permissions DB
```

**Important** : `RoleChecker` et `ScopedRoleChecker` comparent avec les noms d'enum Python (`"ADMIN"`, `"SUPER_ADMIN"`), pas les valeurs JWT lisibles (`"Admin"`, `"Super Admin"`). Superadmin bypass automatique sur tous les guards.

### Casbin RBAC with domains

Le moteur Casbin est initialisé au démarrage (`lifespan`) depuis la DB :

```
Modèle RBAC with domains :
  (sub, dom, obj, act)
  sub  = user.id
  dom  = ministere_id ou '*' (global)
  obj  = ressource : "planning", "chants", "admin"
  act  = "read" | "write"
```

Policies par rôle : `(ADMIN, *, planning, write)`, `(MEMBRE_MLA, *, chants, read)`, etc.

Groupings : chaque `AffectationRole` active génère `g(user_id, role, ministere_id)` ou `g(user_id, role, *)` si sans contexte.

Dégradation gracieuse : si `build_enforcer()` échoue au boot, les guards repassent sur `RoleChecker` sans bloquer l'application.

### `get_active_campus`

Dépendance de résolution du campus actif :

1. Header `X-Campus-Id` (priorité)
2. `campus_principal_id` du membre
3. Vérification `MembreCampusLink` (l'user appartient bien à ce campus)
4. Super Admin : bypass du check d'appartenance

Lève `AUTH_CAMPUS_REQUIRED` (400) ou `AUTH_CAMPUS_FORBIDDEN` (403) selon le cas.

### Capabilities dans le JWT

Le payload JWT contient désormais un champ `capabilities` : liste des codes de permission (`["MEMBRE_READ", "PLANNING_WRITE", …]`). Cela évite un aller-retour DB à chaque check de permission. `CapabilityChecker` lit ce champ en priorité, avec fallback sur les permissions DB pour les tokens émis avant ce changement.

### Implémentation frontend

```typescript
// useAuthStore.ts — computed réactifs
const isSuperAdmin  = computed(() => user.value?.roles?.includes('Super Admin') ?? false)
const isAdmin       = computed(() => user.value?.roles?.includes('Admin') ?? false)
const isResponsable = computed(() => user.value?.roles?.includes('Responsable MLA') ?? false)
const hasAdminAccess   = computed(() => isSuperAdmin.value || isAdmin.value)
const canManageChants  = computed(() => isSuperAdmin.value || isAdmin.value || isResponsable.value)
```

Middleware Nuxt :
- `01.auth.global.ts` — Vérifie l'expiration, hydrate le store au rechargement, redirige vers `/login`
- `02.admin.global.ts` — Protège toutes les routes `/admin/*`, vérifie `hasAdminAccess`

---

## Isolation des données (Multi-tenant)

### Deux dimensions d'isolation

```
Utilisateur → MembreCampusLink    → [Campus A, Campus B]
           └─ MembreMinistereLink → [Louange, Technique]
```

- Chaque requête planning est filtrée par `campus_id` **ou** `ministere_id` de l'utilisateur courant
- Un utilisateur ne peut jamais lire les données d'un campus auquel il n'appartient pas
- La table `CampusMinistereLink` doit exister pour chaque couple (campus, ministère) — contrôlée à la création

### Exception : Répertoire de chants

Le module Songbook est un répertoire commun à tous les campus — pas de filtre `campus_id` appliqué. Ce choix est intentionnel et documenté.

### Vérification côté service

```python
# Exemple : accès à un template — vérification de visibilité
def _is_visible(template, user) -> bool:
    if template.visibilite == "PRIVE":
        return template.createur_id == user.id
    if template.visibilite == "MINISTERE":
        return (template.campus_id == user.campus_id
                and shared_ministere(template, user))
    if template.visibilite == "CAMPUS":
        return template.campus_id == user.campus_id
    return False
```

---

## Gestion des erreurs

### Pas de fuite d'information

- Toutes les erreurs suivent le format unifié `{ error: { code, message, status } }`
- Les messages sont génériques — pas de détail technique (stack trace, SQL) exposé au client
- L'`ErrorRegistry` centralise tous les messages : un seul endroit pour les auditer

### Exceptions métier vs HTTP

```python
# Correct — message contrôlé
raise AppException(ErrorRegistry.AUTH_001)  # → 401 "Identifiants invalides"

# Interdit dans les services
raise HTTPException(status_code=400, detail=str(e))  # → fuite possible
```

---

## Variables d'environnement sensibles

| Variable | Usage | Stockage |
|---|---|---|
| `JWT_SECRET_KEY` | Signature des tokens | Variable d'env uniquement |
| `DATABASE_URL` | Connexion PostgreSQL | Variable d'env uniquement |
| `ALLOWED_ORIGINS` | CORS whitelist | Variable d'env uniquement |

Ces valeurs ne sont **jamais** présentes dans le code source ni dans le dépôt git.

---

## CORS

```python
# backend/src/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # Whitelist explicite — pas de "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

En production : `ALLOWED_ORIGINS` doit contenir uniquement le domaine du frontend.

---

## Points à renforcer avant mise en production

| Priorité | Item | Action recommandée |
|---|---|---|
| 🔴 Critique | `print()` dans `generic_exception_handler` | Remplacer par `logging.getLogger(__name__).exception(exc)` |
| 🔴 Critique | Rate limiting absent | Ajouter `slowapi` ou un reverse proxy (Nginx/Cloudflare) sur `/auth/token` |
| 🟠 Important | Rotation de `JWT_SECRET_KEY` | Mettre en place un mécanisme de rotation sans casser les sessions actives |
| 🟠 Important | Audit log des actions sensibles | Logger les connexions, créations/suppressions de planning, changements de rôle |
| 🟡 Moyen | HTTPS only enforcement | Redirection HTTP→HTTPS via Nginx ou Render settings |
| 🟡 Moyen | Politique de mot de passe | Actuellement aucune validation de complexité côté API |
| 🟡 Moyen | Expiration refresh token | Vérifier que les refresh tokens expirés sont bien nettoyés de la table `t_revoked_tokens` |
| 🟢 Faible | Content Security Policy | Ajouter un header CSP via Nuxt `routeRules` |
| 🟢 Faible | Dependency scanning | Intégrer `pip-audit` et `pnpm audit` dans la CI |

---

## Ce qui est déjà en place (résumé)

- ✅ JWT HS256 avec JTI blacklist (révocation immédiate au logout)
- ✅ Cookies `HttpOnly` + `sameSite: strict` + `secure: true`
- ✅ RBAC déclaratif via `RoleChecker` injectable (+ `ScopedRoleChecker` par ministère)
- ✅ Moteur Casbin RBAC with domains — policies dynamiques sans redéploiement
- ✅ `CapabilityChecker` — vérification granulaire des permissions via JWT
- ✅ `get_active_campus` — résolution et validation du campus actif (`X-Campus-Id`)
- ✅ Isolation multi-tenant par campus et ministère
- ✅ Validité temporelle des affectations vérifiée à chaque check de rôle
- ✅ Zéro `HTTPException` dans les services — erreurs contrôlées via `ErrorRegistry`
- ✅ CORS whitelist explicite
- ✅ Secrets exclusivement via variables d'environnement
- ✅ `actif` vérifié à chaque requête (compte désactivé → 403 immédiat)
- ✅ mypy strict — pas de `Any` implicite dans la couche sécurité

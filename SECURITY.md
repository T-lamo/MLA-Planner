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

```python
# Injection via FastAPI Depends — déclaratif par endpoint
router.get("/planning/full", dependencies=[Depends(RoleChecker(["ADMIN", "RESPONSABLE_MLA"]))])

# RoleChecker extrait les rôles depuis le payload JWT
# Superadmin bypass automatique : si SUPER_ADMIN dans les rôles → toutes les vérifications passent
```

**Important** : `RoleChecker` compare avec les noms d'enum Python (`"ADMIN"`, `"SUPER_ADMIN"`) et non les valeurs JWT lisibles (`"Admin"`, `"Super Admin"`). La conversion est faite à l'intérieur du checker.

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
- ✅ RBAC déclaratif via `RoleChecker` injectable
- ✅ Isolation multi-tenant par campus et ministère
- ✅ Zéro `HTTPException` dans les services — erreurs contrôlées via `ErrorRegistry`
- ✅ CORS whitelist explicite
- ✅ Secrets exclusivement via variables d'environnement
- ✅ `actif` vérifié à chaque requête (compte désactivé → 403 immédiat)
- ✅ mypy strict — pas de `Any` implicite dans la couche sécurité

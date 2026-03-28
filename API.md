# API Reference — MLA Planner

**Base URL** : `http://localhost:8000` (dev) · `https://<your-domain>` (prod)

**Interactive docs** : `GET /docs` (Swagger UI) · `GET /redoc` (ReDoc)

---

## Authentication

### Obtain a token

```http
POST /auth/token
Content-Type: application/json

{
  "username": "amos",
  "password": "plan123!"
}
```

Response:
```json
{
  "token": "<jwt>",
  "refreshToken": "<refresh-jwt>",
  "expiresAt": "2026-04-01T12:00:00Z",
  "user": {
    "id": "...",
    "username": "amos",
    "roles": ["Admin"],
    "capabilities": ["MEMBRE_READ", "PLANNING_WRITE", "CHANT_READ"]
  }
}
```

The `capabilities` array contains permission codes for the user. The frontend reads this to guard UI elements without additional API calls.

### Use the token

```http
Authorization: Bearer <jwt>
```

Or via cookies (`auth_token`) — used by the frontend with `sameSite: strict, secure: true`.

### Refresh

```http
POST /auth/refresh
Authorization: Bearer <refresh-jwt>
```

### Logout

```http
POST /auth/logout
Authorization: Bearer <jwt>
```

Immediately revokes the token JTI in the blacklist.

---

## Response format

### Success

Endpoints that return a single resource:
```json
{ "id": "...", "nom": "...", ... }
```

Paginated lists:
```json
{
  "total": 42,
  "limit": 50,
  "offset": 0,
  "data": [ ... ]
}
```

### Error

All errors follow the same envelope:
```json
{
  "error": {
    "code": "PLAN_001",
    "message": "Ce planning ne peut plus être modifié.",
    "status": 409
  }
}
```

The frontend reads `error.error.code` to handle specific cases.

---

## Endpoints

### Auth — `/auth`

| Method | Path | Description | Roles |
|---|---|---|---|
| POST | `/auth/token` | Login | Public |
| POST | `/auth/logout` | Revoke token | Authenticated |
| POST | `/auth/refresh` | Refresh token | Authenticated |
| GET | `/auth/users/me` | Current user + capabilities | Authenticated |
| PATCH | `/auth/utilisateurs/{id}/password` | Change password | Owner or Admin |

The `GET /auth/users/me` response includes a `capabilities` field (list of permission codes):

```json
{
  "id": "...",
  "username": "amos",
  "roles": ["Admin"],
  "capabilities": ["MEMBRE_READ", "PLANNING_WRITE", "CHANT_READ"],
  "campus_principal_id": "..."
}
```

---

### Profile — `/profil`

| Method | Path | Description | Roles |
|---|---|---|---|
| GET | `/profil/me` | Current user profile | All |
| PATCH | `/profil/me` | Update own profile | All |
| GET | `/profil/me/campuses` | Current user's campuses | All |
| GET | `/profil/me/ministeres/by-campus/{campus_id}` | User's ministries | All |
| GET | `/profil/campus/{campus_id}/` | Paginated profiles by campus | Admin+ |
| GET | `/profil/campus/{campus_id}/all` | All profiles for campus | Admin+ |

---

### Planning — `/planning`

| Method | Path | Description | Roles |
|---|---|---|---|
| GET | `/planning/my/calendar` | Current user's calendar | All |
| GET | `/planning/by-ministere/{ministere_id}` | Plannings by ministry | All |
| GET | `/planning/by-campus/{campus_id}` | Plannings by campus | All |
| POST | `/planning/full` | Create complete planning | Admin, Responsable |
| GET | `/planning/{planning_id}/full` | Full planning details | All |
| PATCH | `/planning/{planning_id}/full` | Update planning + slots | Admin, Responsable |
| PATCH | `/planning/{planning_id}/status` | Change workflow status | Admin, Responsable |
| DELETE | `/planning/{planning_id}/full` | Delete planning | Admin, Responsable |
| POST | `/planning/{planning_id}/slots` | Add slot | Admin, Responsable |

**Status values** : `BROUILLON` · `PUBLIE` · `ANNULE` · `TERMINE`

---

### Planning Templates — `/planning-templates`

| Method | Path | Description | Roles |
|---|---|---|---|
| GET | `/planning-templates` | List templates (with visibility filter) | All |
| POST | `/planning-templates/preview-series` | Preview series dates | Admin, Responsable |
| POST | `/planning-templates/generate-series` | Generate series | Admin, Responsable |
| POST | `/planning-templates/from-planning/{planning_id}` | Save planning as template | Admin, Responsable |
| GET | `/planning-templates/{template_id}` | Template details | All |
| PUT | `/planning-templates/{template_id}` | Replace template | Admin, Responsable |
| PATCH | `/planning-templates/{template_id}` | Partial update | Admin, Responsable |
| POST | `/planning-templates/{template_id}/duplicate` | Duplicate | Admin, Responsable |
| DELETE | `/planning-templates/{template_id}` | Delete | Admin, Responsable |
| POST | `/planning-templates/{template_id}/apply/{planning_id}` | Apply to planning | Admin, Responsable |

**Template visibility** : `PRIVE` · `MINISTERE` · `CAMPUS`

---

### Assignments — `/affectations`

| Method | Path | Description | Roles |
|---|---|---|---|
| PATCH | `/affectations/{id}/my-status` | Update own assignment status | Membre+ |
| PATCH | `/affectations/{id}/status` | Admin status change | Admin, Responsable |

**Status values** : `PROPOSE` · `CONFIRME` · `REFUSE` · `PRESENT`

---

### Songbook — `/chants`

| Method | Path | Description | Roles |
|---|---|---|---|
| GET | `/chants` | List songs (paginated) | All authenticated |
| POST | `/chants` | Create song | Admin, Responsable |
| GET | `/chants/{id}` | Song details | All authenticated |
| PATCH | `/chants/{id}` | Update song | Admin, Responsable |
| DELETE | `/chants/{id}` | Delete song | Admin, Responsable |
| GET | `/chants/{id}/contenu` | ChordPro content | All authenticated |
| PUT | `/chants/{id}/contenu` | Replace content | Admin, Responsable |
| PATCH | `/chants/{id}/contenu` | Patch content | Admin, Responsable |
| POST | `/chants/{id}/contenu/transpose` | Transpose (preview only) | All authenticated |
| GET | `/chants/categories` | List categories | All authenticated |
| POST | `/chants/categories` | Create category | Admin, Responsable |
| PATCH | `/chants/categories/{code}` | Update category | Admin, Responsable |
| DELETE | `/chants/categories/{code}` | Delete category | Admin, Responsable |

Query params for `GET /chants` : `campus_id` (optional filter) · `categorie_code` · `artiste` · `q` (title search) · `limit` · `offset`

---

### Members — `/membres`

| Method | Path | Description | Roles |
|---|---|---|---|
| GET | `/membres/by-ministere/{ministere_id}` | Members by ministry | Admin, Responsable |
| GET | `/membres/me/agenda` | My full agenda | All |
| GET | `/membres/{id}/roles` | Member competences | Admin+ |
| POST | `/membres/{id}/roles` | Add competence | Admin+ |
| DELETE | `/membres/{id}/roles/{role_code}` | Remove competence | Admin+ |

---

### Unavailability — `/indisponibilites`

| Method | Path | Description | Roles |
|---|---|---|---|
| POST | `/indisponibilites/` | Declare unavailability | All |
| GET | `/indisponibilites/me` | My unavailabilities | All |
| DELETE | `/indisponibilites/{id}` | Delete own unavailability | All |
| GET | `/indisponibilites/campus/{campus_id}` | Campus unavailabilities | Admin, Responsable |
| PATCH | `/indisponibilites/{id}/valider` | Validate unavailability | Admin, Responsable |

---

### Admin — `/admin` (Admin+)

| Method | Path | Description | Roles |
|---|---|---|---|
| GET | `/admin/capabilities` | List all available capability codes | Admin+ |
| GET | `/admin/roles` | List roles with their permissions | Admin+ |
| POST | `/admin/roles` | Create a new role | Admin+ |
| DELETE | `/admin/roles/{role_id}` | Delete role (forbidden if assigned) | Admin+ |
| PATCH | `/admin/roles/{role_id}/permissions` | Replace role permissions | Admin+ |

---

### Campus Config — `/campus-config` (Super Admin)

| Method | Path | Description |
|---|---|---|
| GET | `/campus-config/campus` | List all campuses |
| GET | `/campus-config/campus/{campus_id}/summary` | Campus configuration summary |
| POST | `/campus-config/campus/{campus_id}/setup` | Initial campus setup |
| POST | `/campus-config/campus/{campus_id}/ministeres` | Add ministry to campus |
| POST | `/campus-config/campus/{campus_id}/ministeres/{ministere_id}/rbac-roles/init` | Init RBAC roles |

---

## Error codes reference

| Domain | Code | HTTP | Description |
|---|---|---|---|
| **Planning** | `PLAN_001` | 409 | Planning immutable (status prevents modification) |
| | `PLAN_002` | 400 | Planning not published |
| | `PLAN_003` | 404 | Planning or activity not found |
| | `PLAN_012` | 422 | Can't publish without assigned members |
| **Slot** | `SLOT_002` | 422 | Slot out of activity bounds |
| | `SLOT_003` | 422 | Chronology error |
| | `SLOT_004` | 404 | Slot not found |
| **Assignment** | `ASGN_006` | 422 | Member missing required competence |
| | `ASGN_007` | 409 | Forbidden status transition |
| | `ASGN_008` | 403 | Not owner of assignment |
| **Auth** | `AUTH_001` | 401 | Invalid credentials |
| | `AUTH_002` | 403 | Account disabled |
| | `AUTH_004` | 400 | Current password incorrect |
| | `AUTH_006` | 401 | Refresh token invalid/expired |
| | `AUTH_007` | 400 | Active campus required (`X-Campus-Id` missing) |
| | `AUTH_008` | 403 | Campus access forbidden |
| **Config** | `CONF_002` | 409 | Ministry already linked to campus |
| | `CONF_004` | 409 | Role code conflict |
| **Member** | `MEMBRE_003` | 422 | Must be attached to at least 1 campus |
| **Songbook** | `SONG_003` | 422 | Category has songs (can't delete) |
| | `SONG_006` | 409 | Content version conflict |
| | `SONG_007` | 422 | Semitones out of range [-12, 12] |
| **Series** | `SERIE_001` | 422 | Max 52 plannings per batch exceeded |
| | `SERIE_003` | 422 | `jour_semaine` required for weekly recurrence |
| **Template** | `TMPL_003` | 404 | Template not found |
| | `TMPL_004` | 403 | Insufficient access to template |
| **Workflow** | `WKFL_001` | 409 | Invalid status transition |
| **Core** | `CORE_001` | 404 | Resource not found |
| | `CORE_004` | 400 | Integrity error |
| | `CORE_006` | 409 | Resource already exists |
| | `CORE_007` | 409 | Resource in use (cannot delete) |

---

## Roles

| Role | Value in JWT | Permissions |
|---|---|---|
| Super Admin | `Super Admin` | Full access + campus configuration |
| Admin | `Admin` | Full planning + member management on assigned campuses |
| Responsable MLA | `Responsable MLA` | Create/manage plannings, templates, assignments |
| Membre MLA | `Membre MLA` | Read plannings, manage own assignments + unavailabilities |

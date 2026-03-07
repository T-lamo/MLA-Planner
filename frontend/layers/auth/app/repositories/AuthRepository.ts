import { BaseRepository } from '~~/layers/base/app/repositories/BaseRepository'

// --- Interfaces DTO (Data Transfer Objects) ---

/**
 * Structure exacte retournée par ton FastAPI (OAuth2 / Snake Case)
 */
interface RoleSchema {
  id: string
  libelle: string
}

interface LoginSchema {
  access_token: string
  token_type: string
  expires_at: string
  refresh_token: string | null
  user: {
    id: string
    username: string
    actif: boolean
    membre_id: string
    campus_principal_id?: string | null
    name?: string
    roles: RoleSchema[]
  }
}

interface MeSchema {
  id: string
  username: string
  actif: boolean
  membre_id: string
  campus_principal_id?: string | null
  name?: string
  roles: string[]
}

/**
 * Modèle propre pour le Frontend (Camel Case & Clean)
 */
export interface AuthUser {
  id: string
  username: string
  isActive: boolean
  membreId: string
  campusPrincipalId?: string | null
  roles: string[]
  name?: string
}

export interface AuthResponse {
  token: string
  expiresAt: string
  user: AuthUser
}

// --- Implémentation du Repository ---

export class AuthRepository extends BaseRepository {
  /**
   * Authentification utilisateur
   */
  async login(credentials: Record<'username' | 'password', string>): Promise<AuthResponse> {
    const { data } = await this.apiRequest<LoginSchema, AuthResponse>('/auth/token', {
      method: 'POST',
      body: credentials,
      headers: {
        // Indispensable pour que FastAPI reconnaisse le format
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      transform: (response): AuthResponse => ({
        token: response.access_token,
        expiresAt: response.expires_at,
        user: {
          id: response.user.id,
          username: response.user.username,
          isActive: response.user.actif,
          membreId: response.user.membre_id,
          campusPrincipalId: response.user.campus_principal_id ?? null,
          name: response.user.name ?? response.user.username,
          roles: response.user.roles.map((r) => r.libelle),
        },
      }),
    })

    if (!data) throw new Error('Données de connexion introuvables')

    return data
  }

  /**
   * Récupération du profil actuel
   */
  async getMe(): Promise<AuthUser> {
    // Note : /auth/users/me renvoie généralement l'objet "user" directement
    const { data } = await this.apiRequest<MeSchema, AuthUser>('/auth/users/me', {
      method: 'GET',
      transform: (user): AuthUser => ({
        id: user.id,
        username: user.username,
        isActive: user.actif,
        membreId: user.membre_id,
        campusPrincipalId: user.campus_principal_id ?? null,
        name: user.name ?? user.username,
        roles: user.roles ?? [],
      }),
    })

    if (!data) throw new Error('Profil utilisateur introuvable')

    return data
  }

  /**
   * Déconnexion
   */
  async logout() {
    // On passe unknown car on n'attend pas de retour spécifique
    return await this.apiRequest<unknown>('/auth/logout', { method: 'POST' })
  }
}

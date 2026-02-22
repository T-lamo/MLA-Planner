import { BaseRepository } from '~~/layers/base/app/repositories/BaseRepository'

// --- Interfaces DTO (Data Transfer Objects) ---

/**
 * Structure exacte retournée par ton FastAPI (OAuth2 / Snake Case)
 */
interface LoginSchema {
  access_token: string
  token_type: string
  expires_at: string
  refresh_token: string | null
  user: {
    id: string // UUID string
    username: string // Correspond à full_name précédemment
    actif: boolean // Correspond à is_active précédemment
    membre_id: string // UUID lié à l'entité Membre
    roles: string[]
  }
}

/**
 * Modèle propre pour le Frontend (Camel Case & Clean)
 */
export interface AuthUser {
  id: string
  username: string
  isActive: boolean
  membreId: string
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
    // Note : /auth/me renvoie généralement l'objet "user" directement
    const { data } = await this.apiRequest<LoginSchema['user'], AuthUser>('/auth/me', {
      method: 'GET',
      transform: (user): AuthUser => ({
        id: user.id,
        username: user.username,
        isActive: user.actif,
        membreId: user.membre_id,
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

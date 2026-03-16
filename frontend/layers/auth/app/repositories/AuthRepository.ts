import { BaseRepository } from '~~/layers/base/app/repositories/BaseRepository'

// --- Interfaces DTO (Data Transfer Objects) ---

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
  refreshToken: string | null
  user: AuthUser
}

// --- Transform partagé ---

function transformLoginSchema(response: LoginSchema): AuthResponse {
  return {
    token: response.access_token,
    expiresAt: response.expires_at,
    refreshToken: response.refresh_token,
    user: {
      id: response.user.id,
      username: response.user.username,
      isActive: response.user.actif,
      membreId: response.user.membre_id,
      campusPrincipalId: response.user.campus_principal_id ?? null,
      name: response.user.name ?? response.user.username,
      roles: response.user.roles.map((r) => r.libelle),
    },
  }
}

// --- Implémentation du Repository ---

export class AuthRepository extends BaseRepository {
  async login(credentials: Record<'username' | 'password', string>): Promise<AuthResponse> {
    const { data } = await this.apiRequest<LoginSchema, AuthResponse>('/auth/token', {
      method: 'POST',
      body: new URLSearchParams(credentials),
      transform: transformLoginSchema,
    })

    if (!data) throw new Error('Données de connexion introuvables')

    return data
  }

  async refresh(refreshToken: string): Promise<AuthResponse> {
    const { data } = await this.apiRequest<LoginSchema, AuthResponse>('/auth/refresh', {
      method: 'POST',
      body: { refresh_token: refreshToken },
      transform: transformLoginSchema,
    })

    if (!data) throw new Error('Rafraîchissement du token échoué')

    return data
  }

  async getMe(): Promise<AuthUser> {
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

  async logout() {
    return await this.apiRequest<unknown>('/auth/logout', { method: 'POST' })
  }
}

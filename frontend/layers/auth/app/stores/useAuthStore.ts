import { defineStore } from 'pinia'
import type { AuthUser } from '../repositories/AuthRepository'

export const useAuthStore = defineStore('auth', () => {
  // --- ÉTAT (STATE) ---
  // secure: true bloque les cookies sur HTTP (Docker local) — conditionnel au protocole
  const isSecure = import.meta.server
    ? useRequestURL().protocol === 'https:'
    : location.protocol === 'https:'

  const cookieOptions = {
    maxAge: 60 * 60 * 24 * 7,
    path: '/',
    sameSite: 'strict' as const,
    secure: isSecure,
  }

  const token = useCookie<string | null>('auth_token', cookieOptions)
  const user = useCookie<AuthUser | null>('auth_user', cookieOptions)
  const expiresAt = useCookie<string | null>('auth_expires_at', cookieOptions)
  const refreshToken = useCookie<string | null>('auth_refresh_token', cookieOptions)

  // --- GETTERS (COMPUTED) ---
  const isAuthenticated = computed(() => {
    if (!token.value || !expiresAt.value) return false

    const expirationDate = new Date(expiresAt.value)
    const now = new Date()

    return now < expirationDate
  })

  const currentUser = computed(() => user.value)

  /** Vérifie si l'utilisateur possède la capability donnée. */
  function can(capability: string): boolean {
    return user.value?.capabilities?.includes(capability) ?? false
  }

  const isSuperAdmin = computed(() => can('SYSTEM_MANAGE'))
  const isAdmin = computed(() => can('CAMPUS_ADMIN') && !can('SYSTEM_MANAGE'))
  const isResponsableMLA = computed(() => can('PLANNING_WRITE') && !can('CAMPUS_ADMIN'))
  const hasAdminAccess = computed(() => can('CAMPUS_ADMIN'))

  /** Droits module Carnet de chants. */
  const canManageChants = computed(() => can('CHANT_WRITE'))

  /** Droits module Planning — indépendant de canManageChants. */
  const canManagePlanning = computed(() => can('PLANNING_WRITE'))

  // --- ACTIONS ---

  async function login(credentials: Record<'username' | 'password', string>) {
    const { $api } = useNuxtApp()

    const response = await $api.auth.login(credentials)

    token.value = response.token
    user.value = response.user
    expiresAt.value = response.expiresAt
    refreshToken.value = response.refreshToken

    return response
  }

  /**
   * Rafraîchit silencieusement la session (rotation du refresh token).
   * Retourne true si réussi, false sinon (dégradation gracieuse si pas de refresh token).
   */
  async function silentRefresh(): Promise<boolean> {
    if (!refreshToken.value) return false

    try {
      const { $api } = useNuxtApp()
      const response = await $api.auth.refresh(refreshToken.value)

      token.value = response.token
      user.value = response.user
      expiresAt.value = response.expiresAt
      refreshToken.value = response.refreshToken

      return true
    } catch {
      clearLocalAuth()
      return false
    }
  }

  async function initAuth() {
    if (!isAuthenticated.value) {
      if (token.value) clearLocalAuth()
      return
    }

    if (!user.value) {
      await fetchMe()
    }
  }

  /**
   * Récupération des infos profil depuis le serveur
   */
  async function fetchMe(): Promise<void> {
    const { $api } = useNuxtApp()

    if (!token.value) return

    try {
      const userData = await $api.auth.getMe()
      user.value = userData
    } catch (error: unknown) {
      const fetchError = error as { status?: number }

      if (fetchError.status === 401) {
        await logout(false)
      }
    }
  }

  /**
   * Nettoyage local des credentials (Sans appel API)
   */
  function clearLocalAuth() {
    token.value = null
    user.value = null
    expiresAt.value = null
    refreshToken.value = null
  }

  /**
   * Déconnexion complète
   */
  async function logout(shouldRedirect = true, currentPath?: string): Promise<void> {
    const { $api } = useNuxtApp()

    if (token.value) {
      await $api.auth.logout().catch(() => {})
    }

    clearLocalAuth()

    if (shouldRedirect && currentPath !== '/login') {
      await navigateTo('/login')
    }
  }

  return {
    token,
    user,
    expiresAt,
    refreshToken,
    isAuthenticated,
    isSuperAdmin,
    isAdmin,
    isResponsableMLA,
    hasAdminAccess,
    canManageChants,
    canManagePlanning,
    can,
    currentUser,
    login,
    logout,
    fetchMe,
    initAuth,
    clearLocalAuth,
    silentRefresh,
  }
})

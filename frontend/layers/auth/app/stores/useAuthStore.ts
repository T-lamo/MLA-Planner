import { defineStore } from 'pinia'
import type { AuthUser } from '../repositories/AuthRepository'

export const useAuthStore = defineStore('auth', () => {
  const { $api } = useNuxtApp()
  const route = useRoute()

  // --- ÉTAT (STATE) ---
  const cookieOptions = { maxAge: 60 * 60 * 24 * 7, path: '/' }

  const token = useCookie<string | null>('auth_token', cookieOptions)
  const user = useCookie<AuthUser | null>('auth_user', cookieOptions)
  const expiresAt = useCookie<string | null>('auth_expires_at', cookieOptions)

  // --- GETTERS (COMPUTED) ---
  const isAuthenticated = computed(() => {
    if (!token.value || !expiresAt.value) return false

    const expirationDate = new Date(expiresAt.value)
    const now = new Date()

    return now < expirationDate
  })

  const currentUser = computed(() => user.value)

  // --- ACTIONS ---

  async function login(credentials: Record<'username' | 'password', string>) {
    const response = await $api.auth.login(credentials)

    token.value = response.token
    user.value = response.user
    expiresAt.value = response.expiresAt

    return response
  }

  async function initAuth() {
    if (!isAuthenticated.value) {
      if (token.value) await logout(false)
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
    if (!token.value) return

    try {
      const userData = await $api.auth.getMe()
      user.value = userData
    } catch (error: unknown) {
      // ✅ Correction : Utilisation de unknown au lieu de any
      // On transtype l'erreur pour vérifier le status
      const fetchError = error as { status?: number }

      if (fetchError.status === 401) {
        await logout(false)
      }
    }
  }

  /**
   * Déconnexion complète
   */
  async function logout(shouldRedirect = true): Promise<void> {
    if (token.value) {
      await $api.auth.logout().catch(() => {})
    }

    token.value = null
    user.value = null
    expiresAt.value = null

    if (shouldRedirect && route.path !== '/login') {
      await navigateTo('/login')
    }
  }

  return {
    token,
    user,
    expiresAt,
    isAuthenticated,
    currentUser,
    login,
    logout,
    fetchMe,
    initAuth,
  }
})

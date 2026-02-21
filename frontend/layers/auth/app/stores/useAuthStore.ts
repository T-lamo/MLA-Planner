import { defineStore } from 'pinia'
import { useApiFetch } from '~~/layers/base/app/composables/useApiFetch'
import type { User } from '~~/layers/base/types'

interface AuthState {
  user: User | null
  token: string | null
  loading: boolean
}

export const useAuthStore = defineStore('auth', {
  // State : Données brutes
  state: (): AuthState => ({
    user: null,
    token: null,
    loading: false,
  }),

  // Getters : Données dérivées (équivalent des computed)
  getters: {
    isAuthenticated: (state) => !!state.token,
    userRole: (state) => state.user?.role || 'guest',
  },

  // Actions : Logique métier (synchrone ou asynchrone)
  actions: {
    /**
     * Initialisation du store (récupération du token stocké)
     */
    async initAuth() {
      const token = useCookie('auth_token').value
      if (token) {
        this.token = token
        await this.fetchCurrentUser()
      }
    },

    /**
     * Login : Stocke le token et redirige
     */
    async login(credentials: Record<string, string>) {
      this.loading = true
      try {
        // useApiFetch est auto-importé du Base Layer
        const { data, error } = await useApiFetch<{ token: string; user: User }>('/auth/login', {
          method: 'POST',
          body: credentials,
        })

        if (error.value) throw new Error('Identifiants invalides')

        if (data.value) {
          this.token = data.value.token
          this.user = data.value.user

          // Persistance via cookie (sécurisé pour le SSR)
          const tokenCookie = useCookie('auth_token', { maxAge: 60 * 60 * 24 * 7 }) // 7 jours
          tokenCookie.value = data.value.token

          navigateTo('/')
        }
      } finally {
        this.loading = false
      }
    },

    /**
     * Récupération du profil utilisateur (via le token actuel)
     */
    async fetchCurrentUser() {
      const { data } = await useApiFetch<User>('/auth/me')
      if (data.value) {
        this.user = data.value
      } else {
        this.logout()
      }
    },

    /**
     * Logout : Nettoyage complet
     */
    logout() {
      this.user = null
      this.token = null
      useCookie('auth_token').value = null
      navigateTo('/login')
    },
  },
})

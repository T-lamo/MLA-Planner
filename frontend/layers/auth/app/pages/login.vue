<template>
  <div class="flex min-h-screen items-center justify-center bg-slate-50">
    <ui-login
      submitLabel="Accéder à mon compte"
      :loading="isLoading"
      loadingLabel="Vérification..."
      identifierLabel="Identifiant"
      identifierPlaceholder="Ex: MLA-2024"
      passwordLabel="Mot de passe"
      :errorMessage="authError"
      @auth-submit="onLogin"
    >
      <div slot="logo" class="flex flex-col items-center gap-4">
        <h2 class="text-xl font-bold text-slate-800">Espace Membre</h2>
      </div>
    </ui-login>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/useAuthStore'
import type { EnhancedApiError } from '~~/layers/base/types/api'
definePageMeta({
  layout: 'auth', // Utilise le layout vide
})

// Interface pour typer l'événement du Web Component
interface LoginEvent {
  detail: {
    identifier?: string
    password?: string
  }
}

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const { notifyError } = useErrorHandler()

const authError = ref('')
const isLoading = ref(false)

const onLogin = async (event: LoginEvent) => {
  authError.value = ''
  isLoading.value = true

  const { identifier, password } = event.detail

  if (!identifier || !password) {
    isLoading.value = false
    return
  }

  try {
    await authStore.login({
      username: identifier,
      password: password,
    })

    const redirectPath = (route.query.redirect as string) || '/'
    await router.push(redirectPath)
  } catch (error: unknown) {
    // On caste en EnhancedApiError pour le traitement
    const err = error as EnhancedApiError

    // Notification globale (Toast)
    notifyError(err)

    // Mise à jour du message d'erreur interne pour le composant ui-login
    const apiErrorMessage = err?.data?.error?.message || err?.data?.message
    authError.value = apiErrorMessage || 'Une erreur technique est survenue.'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
ui-login {
  --ui-primary: var(--color-primary-600);
  --ui-primary-hover: var(--color-primary-700);
  --ui-radius: 12px;
  --ui-accent: var(--color-accent);
}
</style>

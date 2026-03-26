<template>
  <div class="flex min-h-screen items-center justify-center bg-slate-50">
    <ui-login
      submitLabel="Accéder à mon compte"
      loadingLabel="Vérification..."
      identifierLabel="Identifiant"
      identifierPlaceholder="Ex: MLA-2024"
      passwordLabel="Mot de passe"
      :errorMessage="authError"
      @auth-submit="onLogin"
    >
      <div slot="logo" class="flex flex-col items-center gap-4">
        <img src="/Logo.png" alt="Logo" class="h-16 w-auto object-contain" />
        <h2 class="text-xl font-bold text-slate-800">Espace Membre</h2>
      </div>
    </ui-login>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/useAuthStore'
import { useGlobalLoader } from '~~/layers/base/app/composables/useLoader'
import type { EnhancedApiError } from '~~/layers/base/types/api'

definePageMeta({
  layout: 'auth',
})

// Interface pour typer l'événement du Web Component
interface LoginEvent {
  detail: {
    identifier?: string
    password?: string
  }
}

const authStore = useAuthStore()
const route = useRoute()
// Capturé en setup() synchrone : le contexte Nuxt n'est plus garanti
// dans un callback async déclenché par un CustomEvent Web Component.
const router = useRouter()
const { notifyError } = useErrorHandler()
const { withLoader } = useGlobalLoader()

const authError = ref('')

const onLogin = async (event: LoginEvent) => {
  authError.value = ''

  const { identifier, password } = event.detail
  if (!identifier || !password) return

  await withLoader(async () => {
    try {
      await authStore.login({ username: identifier, password })

      // SuperAdmin → toujours /admin/campuses, ignore le redirect query
      if (authStore.isSuperAdmin) {
        await router.push('/admin/campuses')
        return
      }

      const redirectPath = (route.query.redirect as string) || '/planning/calendar'
      await router.push(redirectPath)
    } catch (error: unknown) {
      const err = error as EnhancedApiError
      notifyError(err)
      const apiErrorMessage = err?.data?.error?.message || err?.data?.message
      authError.value = apiErrorMessage || 'Une erreur technique est survenue.'
    }
  })
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

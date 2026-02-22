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
import { useAuthStore } from '../stores/useAuthStore'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const authError = ref('')
const isLoading = ref(false)

/**
 * Interface pour les données reçues du Web Component
 */
interface AuthSubmitEvent extends Event {
  detail: {
    identifier?: string
    password?: string
  }
}

const onLogin = async (event: AuthSubmitEvent) => {
  authError.value = ''
  isLoading.value = true

  const { identifier, password } = event.detail

  // Sécurité TS : on vérifie que les données existent
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
    // eslint-disable-next-line no-console
    console.error('Erreur Login Page:', error)

    // Assertion de type sécurisée pour l'erreur API
    const fetchError = error as { status?: number }

    if (fetchError.status === 401) {
      authError.value = 'Identifiants incorrects. Veuillez réessayer.'
    } else if (fetchError.status === 422) {
      authError.value = "Format d'identifiant invalide."
    } else {
      authError.value = 'Une erreur technique est survenue.'
    }
  } finally {
    isLoading.value = false
  }
}
</script>
<style scoped>
ui-login {
  --ui-primary: #2563eb;
  --ui-radius: 12px;
}
</style>

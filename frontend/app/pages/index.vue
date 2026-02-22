<template>
  <div class="px-4 py-10 sm:px-6 lg:px-8">
    <div class="mx-auto max-w-4xl">
      <header class="mb-8">
        <h1 class="text-3xl font-extrabold text-slate-900">
          Bienvenue, {{ authStore.currentUser?.username }} !
        </h1>
        <p class="mt-2 text-lg text-slate-600">
          Vous êtes correctement authentifié sur la plateforme MLA.
        </p>
      </header>

      <div class="grid grid-cols-1 gap-6 sm:grid-cols-2">
        <section class="overflow-hidden rounded-lg border border-slate-200 bg-white shadow">
          <div class="p-5">
            <h3 class="mb-4 border-b pb-2 text-lg font-medium text-slate-900">Ma Session</h3>
            <dl>
              <div class="py-2">
                <dt class="text-sm font-medium text-slate-500">ID Utilisateur</dt>
                <dd class="font-mono text-sm text-slate-900">{{ authStore.currentUser?.id }}</dd>
              </div>
              <div class="py-2">
                <dt class="text-sm font-medium text-slate-500">Rôle</dt>
                <dd class="mt-1">
                  <span
                    class="inline-flex rounded-full bg-green-100 px-2 text-xs leading-5 font-semibold text-green-800"
                  >
                    Membre Actif
                  </span>
                </dd>
              </div>
              <div class="py-2">
                <dt class="text-sm font-medium text-slate-500">Expiration du Token</dt>
                <dd class="text-sm text-slate-900">{{ formattedExpiration }}</dd>
              </div>
            </dl>
          </div>
        </section>

        <section class="overflow-hidden rounded-lg border border-slate-200 bg-white shadow">
          <div class="p-5">
            <h3 class="mb-4 border-b pb-2 text-lg font-medium text-slate-900">Navigation</h3>
            <div class="space-y-3">
              <NuxtLink
                to="/planning"
                class="block w-full rounded-md border border-transparent bg-blue-600 px-4 py-2 text-center text-sm font-medium text-white hover:bg-blue-700"
              >
                Consulter mon Planning
              </NuxtLink>
              <button
                class="block w-full rounded-md border border-slate-300 bg-white px-4 py-2 text-center text-sm font-medium text-slate-700 hover:bg-slate-50"
                @click="authStore.logout(true)"
              >
                Me déconnecter
              </button>
            </div>
          </div>
        </section>
      </div>

      <div v-if="isDev" class="mt-10 rounded-lg bg-slate-900 p-4 shadow-inner">
        <h4 class="mb-2 text-xs font-bold tracking-widest text-slate-400 uppercase">
          Raw Store Data (Debug)
        </h4>
        <pre class="overflow-auto text-[10px] text-green-400">{{ authStore.$state }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '~~/layers/auth/app/stores/useAuthStore'

// Initialisation du store
const authStore = useAuthStore()

// Variable pour afficher la zone de debug
const isDev = import.meta.dev
/**
 * Formate la date d'expiration pour l'affichage
 */
const formattedExpiration = computed(() => {
  const expiry = authStore.expiresAt
  if (!expiry) return 'Inconnue'
  return new Date(expiry).toLocaleString('fr-FR', {
    day: '2-digit',
    month: 'long',
    hour: '2-digit',
    minute: '2-digit',
  })
})

// Définition des métadonnées de la page
definePageMeta({
  title: 'Accueil - MLA App',
  // On s'assure que le middleware global traite cette page
})
</script>

<style scoped>
/* Styles spécifiques à la page index si nécessaire */
</style>

<template>
  <div
    v-if="authStore.isAuthenticated"
    class="flex items-center gap-4 border-b bg-white p-4 shadow-sm"
  >
    <div class="flex flex-col">
      <span class="text-sm font-medium text-slate-900">
        {{ authStore.currentUser?.username }}
      </span>
      <span class="text-[10px] font-bold tracking-wider text-slate-400 uppercase">
        Membre #{{ authStore.currentUser?.membreId?.split('-')[0] }}
      </span>
    </div>

    <button
      :disabled="isLoggingOut"
      class="ml-auto rounded-lg bg-slate-800 px-4 py-2 text-sm font-semibold text-white transition-all hover:bg-slate-700 disabled:opacity-50"
      @click="onLogout"
    >
      {{ isLoggingOut ? 'Déconnexion...' : 'Déconnexion' }}
    </button>
  </div>
</template>

<script setup lang="ts">
// On importe le store depuis le layer Auth
import { useAuthStore } from '~~/layers/auth/app/stores/useAuthStore'

const authStore = useAuthStore()
const isLoggingOut = ref(false)

const onLogout = async () => {
  isLoggingOut.value = true
  try {
    await authStore.logout(true)
  } finally {
    isLoggingOut.value = false
  }
}
</script>

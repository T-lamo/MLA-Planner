<template>
  <div class="min-h-screen bg-slate-50">
    <header v-if="authStore.isAuthenticated">
      <UserBar />
    </header>

    <main>
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '~~/layers/auth/app/stores/useAuthStore'
const authStore = useAuthStore()
</script>

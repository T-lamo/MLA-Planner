<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '~~/layers/auth/app/stores/useAuthStore'
import { useCampusConfig } from '~~/layers/base/app/composables/useCampusConfig'

definePageMeta({ layout: 'default' })

const authStore = useAuthStore()

if (!authStore.isSuperAdmin) {
  await navigateTo('/admin/profiles')
}

const { loadCampuses } = useCampusConfig()

onMounted(async () => {
  await loadCampuses()
})
</script>

<template>
  <div class="p-4 md:p-8">
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-slate-900">Configuration des Campus</h1>
        <p class="mt-1 text-sm text-slate-500">
          Gérez les ministères, catégories de compétences et rôles par campus
        </p>
      </div>
    </div>

    <CampusConfigView />
    <CampusConfigDrawer />
  </div>
</template>

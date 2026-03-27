<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '~~/layers/auth/app/stores/useAuthStore'

const props = withDefaults(
  defineProps<{
    /** Capability unique requise (raccourci pour :capabilities="[capability]"). */
    capability?: string
    /** Liste de capabilities à vérifier. */
    capabilities?: string[]
    /** 'any' = au moins une, 'all' = toutes requises. Défaut : 'any'. */
    mode?: 'any' | 'all'
  }>(),
  { capability: undefined, capabilities: undefined, mode: 'any' },
)

const authStore = useAuthStore()

const hasAccess = computed(() => {
  const caps = props.capabilities ?? (props.capability ? [props.capability] : [])
  if (caps.length === 0) return true
  return props.mode === 'all'
    ? caps.every((c) => authStore.can(c))
    : caps.some((c) => authStore.can(c))
})
</script>

<template>
  <slot v-if="hasAccess" />
</template>

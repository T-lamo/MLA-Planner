<template>
  <Transition name="loader-fade">
    <div
      v-if="isLoading"
      class="fixed inset-0 z-[9999] flex items-center justify-center bg-white/60 backdrop-blur-[2px]"
      aria-live="polite"
      aria-label="Chargement en cours"
      role="status"
    >
      <svg
        class="loader-spinner"
        width="40"
        height="40"
        viewBox="0 0 40 40"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <circle cx="20" cy="20" r="16" stroke="var(--color-primary-200)" stroke-width="4" />
        <path
          d="M20 4a16 16 0 0 1 16 16"
          stroke="var(--color-primary-600)"
          stroke-width="4"
          stroke-linecap="round"
        />
      </svg>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { useGlobalLoader } from '../composables/useLoader'

const { isLoading } = useGlobalLoader()
</script>

<style scoped>
@reference "../assets/css/main.css";

.loader-spinner {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.loader-fade-enter-active,
.loader-fade-leave-active {
  transition: opacity 150ms ease;
}

.loader-fade-enter-from,
.loader-fade-leave-to {
  opacity: 0;
}
</style>

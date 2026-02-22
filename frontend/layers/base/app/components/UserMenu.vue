<template>
  <div class="relative w-full">
    <button
      :class="[
        'flex w-full items-center gap-3 rounded-xl p-2 transition-all duration-200 hover:bg-slate-100 active:scale-95',
        collapsed ? 'justify-center' : 'justify-start',
      ]"
      title="Mon compte"
      @click="isDropdownOpen = !isDropdownOpen"
    >
      <div
        class="flex size-10 shrink-0 items-center justify-center rounded-full bg-(--color-primary-600) text-sm font-bold text-white shadow-sm"
      >
        {{ userInitials }}
      </div>

      <div v-if="!collapsed" class="flex flex-1 flex-col overflow-hidden text-left">
        <span class="truncate text-sm font-bold text-slate-900">
          {{ authStore.user?.name || 'Utilisateur MLA' }}
        </span>
        <span class="truncate text-xs text-slate-500">
          {{ authStore.user?.role || 'Responsable' }}
        </span>
      </div>

      <ChevronUp
        v-if="!collapsed"
        :class="['size-4 text-slate-400 transition-transform', isDropdownOpen ? 'rotate-180' : '']"
      />
    </button>

    <Transition name="fade-slide">
      <div
        v-if="isDropdownOpen"
        class="absolute bottom-full left-0 z-50 mb-2 w-full min-w-[200px] overflow-hidden rounded-xl border border-slate-200 bg-white p-1 shadow-xl"
      >
        <div class="px-3 py-2 text-xs font-semibold tracking-wider text-slate-400 uppercase">
          Paramètres
        </div>

        <button class="menu-item" @click="navigate('/profile')">
          <User class="size-4" />
          <span>Mon Profil</span>
        </button>

        <button class="menu-item" @click="navigate('/settings')">
          <Settings class="size-4" />
          <span>Préférences</span>
        </button>

        <div class="my-1 border-t border-slate-100" />

        <button class="menu-item text-red-600 hover:bg-red-50" @click="handleLogout">
          <LogOut class="size-4" />
          <span>Déconnexion</span>
        </button>
      </div>
    </Transition>

    <div
      v-if="isDropdownOpen"
      class="fixed inset-0 z-40 h-full w-full"
      @click="isDropdownOpen = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ChevronUp, User, LogOut, Settings } from 'lucide-vue-next'
import { useAuthStore } from '~~/layers/auth/app/stores/useAuthStore'

// Propriété transmise par le Layout (default.vue)
const _props = defineProps<{
  collapsed: boolean
}>()

const authStore = useAuthStore()
const isDropdownOpen = ref(false)

// Calcul des initiales (ex: "Amos Dorceus" -> "AD")
const userInitials = computed(() => {
  const name = authStore.user?.name || 'Admin'
  return name
    .split(' ')
    .map((word) => word[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
})

// Navigation programmatique
const navigate = (path: string) => {
  isDropdownOpen.value = false
  navigateTo(path)
}

// Logique de déconnexion
const handleLogout = async () => {
  isDropdownOpen.value = false
  try {
    await authStore.logout()
    await navigateTo('/login')
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error('Logout failed:', error)
  }
}
</script>

<style scoped>
/* On importe les références du thème pour que @apply fonctionne.
  Ajuste le chemin selon l'emplacement de ton fichier CSS principal.
*/
@reference "../assets/css/main.css";

.menu-item {
  @apply flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors hover:bg-slate-50;
}

/* Animation du Dropdown */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.2s ease;
}
.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>

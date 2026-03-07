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
          {{ authStore.user?.name || authStore.user?.username || 'Utilisateur' }}
        </span>
        <span class="truncate text-xs text-slate-500">
          {{ authStore.user?.roles?.[0] ?? '' }}
        </span>
      </div>

      <ChevronUp
        v-if="!collapsed"
        :class="['size-4 text-slate-400 transition-transform', isDropdownOpen ? 'rotate-180' : '']"
      />
    </button>

    <div
      v-if="isDropdownOpen"
      class="absolute bottom-full left-0 z-50 mb-2 w-full min-w-[200px] overflow-hidden rounded-xl border border-slate-200 bg-white p-1 shadow-xl"
    >
      <div class="px-3 py-2 text-[10px] font-bold tracking-widest text-slate-400 uppercase">
        Mon compte
      </div>
      <button class="menu-item" @click="navigate('/settings/profile')">
        <User class="size-4" />
        <span>Mon Profil</span>
      </button>

      <div class="my-1 border-t border-slate-100" />

      <button class="menu-item text-red-600 hover:bg-red-50" @click="handleLogout">
        <LogOut class="size-4" />
        <span>Déconnexion</span>
      </button>
    </div>

    <div
      v-if="isDropdownOpen"
      class="fixed inset-0 z-40 h-full w-full"
      @click="isDropdownOpen = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ChevronUp, User, LogOut } from 'lucide-vue-next'
import { useAuthStore } from '~~/layers/auth/app/stores/useAuthStore'

defineProps<{ collapsed: boolean }>()

const authStore = useAuthStore()
const isDropdownOpen = ref(false)

const userInitials = computed(() => {
  const name = authStore.user?.name || authStore.user?.username || '?'
  return name
    .split(' ')
    .map((word) => word[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
})

const navigate = (path: string) => {
  isDropdownOpen.value = false
  navigateTo(path)
}

const handleLogout = async () => {
  isDropdownOpen.value = false
  try {
    await authStore.logout()
    await navigateTo('/login')
  } catch {
    // logout failure is silent — user stays on current page
  }
}
</script>

<style scoped>
@reference "../assets/css/main.css";

.menu-item {
  @apply flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors hover:bg-slate-50;
}
</style>

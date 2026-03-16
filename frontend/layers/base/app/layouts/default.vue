<template>
  <div
    v-if="authStore.isAuthenticated"
    class="flex h-screen overflow-hidden bg-[var(--color-slate-50)] text-slate-900"
  >
    <div
      v-if="!ui.isSidebarCollapsed"
      class="fixed inset-0 z-40 bg-slate-900/20 backdrop-blur-sm md:hidden"
      @click="ui.toggleSidebar"
    ></div>

    <aside
      :class="[
        'fixed inset-y-0 left-0 z-50 flex flex-col border-r border-slate-200 bg-white transition-all duration-300 ease-in-out md:relative',
        ui.isSidebarCollapsed
          ? 'w-0 -translate-x-full md:w-20 md:translate-x-0'
          : 'w-64 translate-x-0',
      ]"
    >
      <div class="flex h-16 shrink-0 items-center justify-between px-6">
        <div v-if="!ui.isSidebarCollapsed" class="flex min-w-0 items-center gap-2">
          <img src="/Logo.png" alt="Logo" class="h-8 w-8 shrink-0 object-contain" />
          <span class="truncate text-xl font-bold text-(--color-primary-700)">Planner</span>
        </div>
        <button
          class="rounded-lg p-1 transition-colors hover:bg-slate-100"
          @click="ui.toggleSidebar"
        >
          <component
            :is="ui.isSidebarCollapsed ? ChevronRight : ChevronLeft"
            class="size-5 text-slate-500"
          />
        </button>
      </div>

      <nav class="custom-scrollbar flex-1 overflow-y-auto px-3 py-4">
        <div class="space-y-4">
          <div v-if="!authStore.isSuperAdmin" class="relative">
            <button
              ref="triggerRef"
              class="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all hover:bg-slate-100"
              :class="[
                isPlanningOpen && !ui.isSidebarCollapsed
                  ? 'bg-slate-50 text-(--color-primary-700)'
                  : 'text-slate-600',
              ]"
              @click="handleMenuClick"
              @mouseenter="handleMouseEnter"
              @mouseleave="handleMouseLeave"
            >
              <CalendarDays class="size-5 shrink-0" />
              <span
                v-if="!ui.isSidebarCollapsed"
                class="flex-1 text-left text-[10px] font-bold tracking-wider uppercase"
                >Planning</span
              >
              <ChevronDown
                v-if="!ui.isSidebarCollapsed"
                :class="[
                  'size-3.5 transition-transform duration-200',
                  isPlanningOpen ? 'rotate-180' : '',
                ]"
              />
            </button>

            <transition name="expand">
              <ul
                v-if="isPlanningOpen && !ui.isSidebarCollapsed"
                class="mt-1 space-y-1 overflow-hidden"
              >
                <SidebarLink
                  to="/planning/calendar"
                  :icon="CalendarDays"
                  label="Vue Calendrier"
                  :collapsed="false"
                  class="pl-9"
                />
                <SidebarLink
                  to="/planning/list"
                  :icon="ListTodo"
                  label="Liste des Plannings"
                  :collapsed="false"
                  :badge="planningStore.draftCount"
                  class="pl-9"
                />
                <SidebarLink
                  v-if="authStore.hasAdminAccess"
                  to="/planning/indisponibilites"
                  :icon="CalendarOff"
                  label="Indisponibilités"
                  :collapsed="false"
                  class="pl-9"
                />
              </ul>
            </transition>

            <Teleport to="body">
              <transition name="fade-in">
                <div
                  v-if="ui.isSidebarCollapsed && isPopupVisible"
                  :style="popupStyle"
                  class="fixed z-[9999] w-56 rounded-xl border border-slate-200 bg-white p-2 shadow-2xl"
                  @mouseenter="cancelClose"
                  @mouseleave="handleMouseLeave"
                >
                  <div
                    class="mb-2 border-b border-slate-50 px-3 py-1 text-[10px] font-bold tracking-widest text-slate-400 uppercase"
                  >
                    Planning
                  </div>
                  <ul class="space-y-1">
                    <SidebarLink
                      to="/planning/calendar"
                      :icon="CalendarDays"
                      label="Vue Calendrier"
                      :collapsed="false"
                      @click="closePopup"
                    />
                    <SidebarLink
                      to="/planning/list"
                      :icon="ListTodo"
                      label="Liste des Plannings"
                      :collapsed="false"
                      :badge="planningStore.draftCount"
                      @click="closePopup"
                    />
                    <SidebarLink
                      v-if="authStore.hasAdminAccess"
                      to="/planning/indisponibilites"
                      :icon="CalendarOff"
                      label="Indisponibilités"
                      :collapsed="false"
                      @click="closePopup"
                    />
                  </ul>
                </div>
              </transition>
            </Teleport>
          </div>
        </div>

        <!-- Section Super Admin (SUPER_ADMIN uniquement) -->
        <div v-if="authStore.isSuperAdmin" class="relative mt-4">
          <button
            ref="superAdminTriggerRef"
            class="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all hover:bg-slate-100"
            :class="[
              isSuperAdminOpen && !ui.isSidebarCollapsed
                ? 'bg-slate-50 text-(--color-primary-700)'
                : 'text-slate-600',
            ]"
            @click="handleSuperAdminMenuClick"
            @mouseenter="handleSuperAdminMouseEnter"
            @mouseleave="handleSuperAdminMouseLeave"
          >
            <Building2 class="size-5 shrink-0" />
            <span
              v-if="!ui.isSidebarCollapsed"
              class="flex-1 text-left text-[10px] font-bold tracking-wider uppercase"
              >Super Admin</span
            >
            <ChevronDown
              v-if="!ui.isSidebarCollapsed"
              :class="[
                'size-3.5 transition-transform duration-200',
                isSuperAdminOpen ? 'rotate-180' : '',
              ]"
            />
          </button>

          <transition name="expand">
            <ul
              v-if="isSuperAdminOpen && !ui.isSidebarCollapsed"
              class="mt-1 space-y-1 overflow-hidden"
            >
              <SidebarLink
                to="/admin/campuses"
                :icon="Building2"
                label="Campuses"
                :collapsed="false"
                class="pl-9"
              />
              <SidebarLink
                to="/admin/campus-config"
                :icon="Settings2"
                label="Config. Campus"
                :collapsed="false"
                class="pl-9"
              />
            </ul>
          </transition>

          <Teleport to="body">
            <transition name="fade-in">
              <div
                v-if="ui.isSidebarCollapsed && isSuperAdminPopupVisible"
                :style="superAdminPopupStyle"
                class="fixed z-[9999] w-56 rounded-xl border border-slate-200 bg-white p-2 shadow-2xl"
                @mouseenter="cancelSuperAdminClose"
                @mouseleave="handleSuperAdminMouseLeave"
              >
                <div
                  class="mb-2 border-b border-slate-50 px-3 py-1 text-[10px] font-bold tracking-widest text-slate-400 uppercase"
                >
                  Super Admin
                </div>
                <ul class="space-y-1">
                  <SidebarLink
                    to="/admin/campuses"
                    :icon="Building2"
                    label="Campuses"
                    :collapsed="false"
                    @click="closeSuperAdminPopup"
                  />
                  <SidebarLink
                    to="/admin/campus-config"
                    :icon="Settings2"
                    label="Config. Campus"
                    :collapsed="false"
                    @click="closeSuperAdminPopup"
                  />
                </ul>
              </div>
            </transition>
          </Teleport>
        </div>

        <!-- Section Administration (ADMIN et SUPER ADMIN uniquement) -->
        <div v-if="authStore.hasAdminAccess" class="relative mt-4">
          <button
            ref="adminTriggerRef"
            class="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all hover:bg-slate-100"
            :class="[
              isAdminOpen && !ui.isSidebarCollapsed
                ? 'bg-slate-50 text-(--color-primary-700)'
                : 'text-slate-600',
            ]"
            @click="handleAdminMenuClick"
            @mouseenter="handleAdminMouseEnter"
            @mouseleave="handleAdminMouseLeave"
          >
            <Users class="size-5 shrink-0" />
            <span
              v-if="!ui.isSidebarCollapsed"
              class="flex-1 text-left text-[10px] font-bold tracking-wider uppercase"
              >Administration</span
            >
            <ChevronDown
              v-if="!ui.isSidebarCollapsed"
              :class="[
                'size-3.5 transition-transform duration-200',
                isAdminOpen ? 'rotate-180' : '',
              ]"
            />
          </button>

          <transition name="expand">
            <ul v-if="isAdminOpen && !ui.isSidebarCollapsed" class="mt-1 space-y-1 overflow-hidden">
              <SidebarLink
                to="/admin/profiles"
                :icon="Users"
                label="Profils"
                :collapsed="false"
                class="pl-9"
              />
            </ul>
          </transition>

          <Teleport to="body">
            <transition name="fade-in">
              <div
                v-if="ui.isSidebarCollapsed && isAdminPopupVisible"
                :style="adminPopupStyle"
                class="fixed z-[9999] w-56 rounded-xl border border-slate-200 bg-white p-2 shadow-2xl"
                @mouseenter="cancelAdminClose"
                @mouseleave="handleAdminMouseLeave"
              >
                <div
                  class="mb-2 border-b border-slate-50 px-3 py-1 text-[10px] font-bold tracking-widest text-slate-400 uppercase"
                >
                  Administration
                </div>
                <ul class="space-y-1">
                  <SidebarLink
                    to="/admin/profiles"
                    :icon="Users"
                    label="Profils"
                    :collapsed="false"
                    @click="closeAdminPopup"
                  />
                </ul>
              </div>
            </transition>
          </Teleport>
        </div>
      </nav>

      <div class="border-t border-slate-100 p-4">
        <UserMenu :collapsed="ui.isSidebarCollapsed" />
      </div>
    </aside>

    <main class="relative z-10 flex min-w-0 flex-1 flex-col overflow-hidden">
      <TopBar />
      <div class="flex-1 overflow-y-auto bg-slate-50 p-4 md:p-6">
        <slot />
      </div>
    </main>
  </div>

  <div v-else class="min-h-screen bg-slate-50">
    <slot />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  Building2,
  CalendarDays,
  CalendarOff,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ListTodo,
  Settings2,
  Users,
} from 'lucide-vue-next'
import { useUIStore } from '../stores/useUiStore'
import { useAuthStore } from '~~/layers/auth/app/stores/useAuthStore'
import { useSessionManager } from '~~/layers/auth/app/composables/useSessionManager'

const ui = useUIStore()
const authStore = useAuthStore()
useSessionManager()

const isPlanningOpen = ref(true)
const isPopupVisible = ref(false)
const triggerRef = ref<HTMLElement | null>(null)
const popupTop = ref(0)
const planningStore = { draftCount: 5 }

let closeTimer: ReturnType<typeof setTimeout> | null = null

// --- Super Admin menu state ---
const isSuperAdminOpen = ref(true)
const isSuperAdminPopupVisible = ref(false)
const superAdminTriggerRef = ref<HTMLElement | null>(null)
const superAdminPopupTop = ref(0)
let superAdminCloseTimer: ReturnType<typeof setTimeout> | null = null

const superAdminPopupStyle = computed(() => ({
  top: `${superAdminPopupTop.value}px`,
  left: '76px',
}))

const updateSuperAdminPopupPosition = () => {
  if (superAdminTriggerRef.value) {
    const rect = superAdminTriggerRef.value.getBoundingClientRect()
    superAdminPopupTop.value = rect.top
  }
}

const handleSuperAdminMenuClick = () => {
  if (ui.isSidebarCollapsed) {
    updateSuperAdminPopupPosition()
    isSuperAdminPopupVisible.value = !isSuperAdminPopupVisible.value
  } else {
    isSuperAdminOpen.value = !isSuperAdminOpen.value
  }
}

const handleSuperAdminMouseEnter = () => {
  if (ui.isSidebarCollapsed) {
    cancelSuperAdminClose()
    updateSuperAdminPopupPosition()
    isSuperAdminPopupVisible.value = true
  }
}

const handleSuperAdminMouseLeave = () => {
  if (ui.isSidebarCollapsed) {
    superAdminCloseTimer = setTimeout(() => {
      isSuperAdminPopupVisible.value = false
    }, 150)
  }
}

const cancelSuperAdminClose = () => {
  if (superAdminCloseTimer) {
    clearTimeout(superAdminCloseTimer)
    superAdminCloseTimer = null
  }
}

const closeSuperAdminPopup = () => {
  cancelSuperAdminClose()
  isSuperAdminPopupVisible.value = false
}

// --- Administration menu state ---
const isAdminOpen = ref(true)
const isAdminPopupVisible = ref(false)
const adminTriggerRef = ref<HTMLElement | null>(null)
const adminPopupTop = ref(0)
let adminCloseTimer: ReturnType<typeof setTimeout> | null = null

const adminPopupStyle = computed(() => ({
  top: `${adminPopupTop.value}px`,
  left: '76px',
}))

const updateAdminPopupPosition = () => {
  if (adminTriggerRef.value) {
    const rect = adminTriggerRef.value.getBoundingClientRect()
    adminPopupTop.value = rect.top
  }
}

const handleAdminMenuClick = () => {
  if (ui.isSidebarCollapsed) {
    updateAdminPopupPosition()
    isAdminPopupVisible.value = !isAdminPopupVisible.value
  } else {
    isAdminOpen.value = !isAdminOpen.value
  }
}

const handleAdminMouseEnter = () => {
  if (ui.isSidebarCollapsed) {
    cancelAdminClose()
    updateAdminPopupPosition()
    isAdminPopupVisible.value = true
  }
}

const handleAdminMouseLeave = () => {
  if (ui.isSidebarCollapsed) {
    adminCloseTimer = setTimeout(() => {
      isAdminPopupVisible.value = false
    }, 150)
  }
}

const cancelAdminClose = () => {
  if (adminCloseTimer) {
    clearTimeout(adminCloseTimer)
    adminCloseTimer = null
  }
}

const closeAdminPopup = () => {
  cancelAdminClose()
  isAdminPopupVisible.value = false
}

const popupStyle = computed(() => ({
  top: `${popupTop.value}px`,
  left: '76px', // Ajusté pour être très proche de la sidebar (80px - 4px de gap)
}))

const updatePopupPosition = () => {
  if (triggerRef.value) {
    const rect = triggerRef.value.getBoundingClientRect()
    popupTop.value = rect.top
  }
}

const handleMenuClick = () => {
  if (ui.isSidebarCollapsed) {
    updatePopupPosition()
    isPopupVisible.value = !isPopupVisible.value
  } else {
    isPlanningOpen.value = !isPlanningOpen.value
  }
}

const handleMouseEnter = () => {
  if (ui.isSidebarCollapsed) {
    cancelClose()
    updatePopupPosition()
    isPopupVisible.value = true
  }
}

const handleMouseLeave = () => {
  if (ui.isSidebarCollapsed) {
    // On lance un timer de 150ms avant de fermer
    closeTimer = setTimeout(() => {
      isPopupVisible.value = false
    }, 150)
  }
}

const cancelClose = () => {
  if (closeTimer) {
    clearTimeout(closeTimer)
    closeTimer = null
  }
}

const closePopup = () => {
  cancelClose()
  isPopupVisible.value = false
}
</script>

<style scoped>
@reference "../assets/css/main.css";

/* Animations */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  max-height: 200px;
}
.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
  transform: translateY(-4px);
}

.fade-in-enter-active,
.fade-in-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}
.fade-in-enter-from,
.fade-in-leave-to {
  opacity: 0;
  transform: translateX(-10px);
}

.custom-scrollbar::-webkit-scrollbar {
  width: 3px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #e2e8f0;
  border-radius: 10px;
}
</style>

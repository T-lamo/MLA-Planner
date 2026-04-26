<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { Component } from 'vue'
import {
  Activity,
  Building2,
  CalendarDays,
  CalendarOff,
  Check,
  CheckCircle2,
  ChevronDown,
  Crown,
  GitBranch,
  Landmark,
  LayoutTemplate,
  Loader2,
  Music,
  Plus,
  RotateCcw,
  Settings2,
  ShieldAlert,
  ShieldCheck,
  Trash2,
  User,
  UserCog,
  Users,
} from 'lucide-vue-next'
import { useAuthStore } from '~~/layers/auth/app/stores/useAuthStore'
import { useRoleStore } from '~~/layers/base/app/stores/useRoleStore'
import RoleDrawer from '~~/layers/base/app/components/admin/RoleDrawer.vue'
import CanGuard from '~~/layers/base/app/components/ui/CanGuard.vue'

definePageMeta({ layout: 'default' })

const authStore = useAuthStore()
if (!authStore.can('CAMPUS_ADMIN')) await navigateTo('/admin/profiles')

const roleStore = useRoleStore()
onMounted(() => roleStore.fetchAdminData())

// ─── État accordéon ────────────────────────────────────────────────
const openRole = ref<string | null>(null)

function toggle(roleId: string) {
  openRole.value = openRole.value === roleId ? null : roleId
  ensureLocal(roleId)
}

// ─── Sélections locales (dirty state) ──────────────────────────────
const localSelections = ref<Record<string, Set<string>>>({})
const savedRoles = ref<Set<string>>(new Set())

function ensureLocal(roleId: string) {
  if (localSelections.value[roleId]) return
  const role = roleStore.rolesWithPermissions.find((r) => r.id === roleId)
  localSelections.value[roleId] = new Set(role?.permissions.map((p) => p.code) ?? [])
}

function isChecked(roleId: string, code: string): boolean {
  return localSelections.value[roleId]
    ? localSelections.value[roleId].has(code)
    : (roleStore.rolesWithPermissions
        .find((r) => r.id === roleId)
        ?.permissions.some((p) => p.code === code) ?? false)
}

function handleToggle(roleId: string, code: string) {
  ensureLocal(roleId)
  const set = localSelections.value[roleId]
  if (!set) return
  if (set.has(code)) {
    set.delete(code)
  } else {
    set.add(code)
  }
}

function toggleCategory(roleId: string, codes: string[]) {
  ensureLocal(roleId)
  const set = localSelections.value[roleId]
  if (!set) return
  const allChecked = codes.every((c) => set.has(c))
  codes.forEach((c) => {
    if (allChecked) {
      set.delete(c)
    } else {
      set.add(c)
    }
  })
}

function reset(roleId: string) {
  Reflect.deleteProperty(localSelections.value, roleId)
}

function isDirty(roleId: string): boolean {
  const local = localSelections.value[roleId]
  if (!local) return false
  const original = new Set(
    roleStore.rolesWithPermissions.find((r) => r.id === roleId)?.permissions.map((p) => p.code),
  )
  if (original.size !== local.size) return true
  for (const c of original) if (!local.has(c)) return true
  return false
}

function selectedCount(roleId: string): number {
  return localSelections.value[roleId]
    ? localSelections.value[roleId].size
    : (roleStore.rolesWithPermissions.find((r) => r.id === roleId)?.permissions.length ?? 0)
}

async function save(roleId: string) {
  ensureLocal(roleId)
  await roleStore.updateRolePermissions(roleId, [
    ...(localSelections.value[roleId] ?? new Set<string>()),
  ])
  Reflect.deleteProperty(localSelections.value, roleId)
  savedRoles.value.add(roleId)
  setTimeout(() => savedRoles.value.delete(roleId), 2500)
}

// ─── Métadonnées des rôles ──────────────────────────────────────────
interface RoleMeta {
  icon: Component
  borderClass: string
  badgeClass: string
  iconBgClass: string
  iconColorClass: string
  description: string
}

const ROLE_META: Record<string, RoleMeta> = {
  'Super Admin': {
    icon: Crown,
    borderClass: 'border-l-violet-400',
    badgeClass: 'bg-violet-50 text-violet-700 ring-violet-100',
    iconBgClass: 'bg-violet-100',
    iconColorClass: 'text-violet-600',
    description: 'Accès système complet, sans restriction',
  },
  Admin: {
    icon: ShieldAlert,
    borderClass: 'border-l-amber-400',
    badgeClass: 'bg-amber-50 text-amber-700 ring-amber-100',
    iconBgClass: 'bg-amber-100',
    iconColorClass: 'text-amber-600',
    description: 'Gestion du campus et des utilisateurs',
  },
  'Responsable MLA': {
    icon: Users,
    borderClass: 'border-l-sky-400',
    badgeClass: 'bg-sky-50 text-sky-700 ring-sky-100',
    iconBgClass: 'bg-sky-100',
    iconColorClass: 'text-sky-600',
    description: 'Gestion du planning et du répertoire',
  },
  'Membre MLA': {
    icon: User,
    borderClass: 'border-l-emerald-400',
    badgeClass: 'bg-emerald-50 text-emerald-700 ring-emerald-100',
    iconBgClass: 'bg-emerald-100',
    iconColorClass: 'text-emerald-600',
    description: 'Consultation et participation aux plannings',
  },
}

const DEFAULT_META: RoleMeta = {
  icon: ShieldCheck,
  borderClass: 'border-l-slate-300',
  badgeClass: 'bg-slate-50 text-slate-700 ring-slate-100',
  iconBgClass: 'bg-slate-100',
  iconColorClass: 'text-slate-500',
  description: 'Rôle personnalisé',
}

function roleMeta(libelle: string): RoleMeta {
  return ROLE_META[libelle] ?? DEFAULT_META
}

// ─── Métadonnées des catégories ─────────────────────────────────────
interface CatMeta {
  icon: Component
  label: string
  chipClass: string
  chipActiveClass: string
}

const CAT_META: Record<string, CatMeta> = {
  CHANT: {
    icon: Music,
    label: 'Répertoire',
    chipClass: 'border-rose-200 text-rose-600 bg-rose-50',
    chipActiveClass: 'ring-1 ring-rose-200',
  },
  PLANNING: {
    icon: CalendarDays,
    label: 'Planning',
    chipClass: 'border-blue-200 text-blue-600 bg-blue-50',
    chipActiveClass: 'ring-1 ring-blue-200',
  },
  TEMPLATE: {
    icon: LayoutTemplate,
    label: 'Templates',
    chipClass: 'border-indigo-200 text-indigo-600 bg-indigo-50',
    chipActiveClass: 'ring-1 ring-indigo-200',
  },
  MEMBRE: {
    icon: Users,
    label: 'Membres',
    chipClass: 'border-teal-200 text-teal-600 bg-teal-50',
    chipActiveClass: 'ring-1 ring-teal-200',
  },
  USER: {
    icon: UserCog,
    label: 'Utilisateurs',
    chipClass: 'border-amber-200 text-amber-700 bg-amber-50',
    chipActiveClass: 'ring-1 ring-amber-200',
  },
  ROLE: {
    icon: ShieldCheck,
    label: 'Rôles',
    chipClass: 'border-violet-200 text-violet-600 bg-violet-50',
    chipActiveClass: 'ring-1 ring-violet-200',
  },
  CAMPUS: {
    icon: Building2,
    label: 'Campus',
    chipClass: 'border-cyan-200 text-cyan-600 bg-cyan-50',
    chipActiveClass: 'ring-1 ring-cyan-200',
  },
  MINISTERE: {
    icon: Landmark,
    label: 'Ministères',
    chipClass: 'border-orange-200 text-orange-600 bg-orange-50',
    chipActiveClass: 'ring-1 ring-orange-200',
  },
  POLE: {
    icon: GitBranch,
    label: 'Pôles',
    chipClass: 'border-lime-200 text-lime-700 bg-lime-50',
    chipActiveClass: 'ring-1 ring-lime-200',
  },
  ACTIVITE: {
    icon: Activity,
    label: 'Activités',
    chipClass: 'border-pink-200 text-pink-600 bg-pink-50',
    chipActiveClass: 'ring-1 ring-pink-200',
  },
  INDISPO: {
    icon: CalendarOff,
    label: 'Indisponibilités',
    chipClass: 'border-red-200 text-red-600 bg-red-50',
    chipActiveClass: 'ring-1 ring-red-200',
  },
  SYSTEM: {
    icon: Settings2,
    label: 'Système',
    chipClass: 'border-slate-200 text-slate-600 bg-slate-50',
    chipActiveClass: 'ring-1 ring-slate-200',
  },
}

const DEFAULT_CAT: CatMeta = {
  icon: ShieldCheck,
  label: '',
  chipClass: 'border-slate-200 text-slate-600 bg-slate-50',
  chipActiveClass: 'ring-1 ring-slate-200',
}

function catMeta(prefix: string): CatMeta {
  return CAT_META[prefix] ?? { ...DEFAULT_CAT, label: prefix }
}

const groupedCapabilities = computed(() => {
  const groups: Record<string, string[]> = {}
  for (const cap of roleStore.capabilities) {
    const prefix = cap.code.split('_')[0] ?? cap.code
    if (!groups[prefix]) groups[prefix] = []
    groups[prefix].push(cap.code)
  }
  return groups
})

const totalCaps = computed(() => roleStore.capabilities.length)

function actionLabel(code: string): string {
  return code.split('_').slice(1).join('_')
}

// ─── Drawer création ────────────────────────────────────────────────
const drawerOpen = ref(false)

// ─── Suppression ────────────────────────────────────────────────────
const deleteError = ref('')

async function confirmDeleteRole(roleId: string) {
  if (!window.confirm('Supprimer ce rôle ? Cette action est irréversible.')) return
  deleteError.value = ''
  try {
    await roleStore.deleteRole(roleId)
    if (openRole.value === roleId) openRole.value = null
  } catch {
    deleteError.value = 'Suppression impossible : ce rôle est peut-être utilisé.'
  }
}
</script>

<template>
  <div class="min-h-screen bg-slate-50/60">
    <!-- ── En-tête ── -->
    <div class="border-b border-slate-200 bg-white px-6 py-5">
      <div class="flex items-center gap-4">
        <div
          class="from-primary-500 to-primary-700 flex size-11 items-center justify-center rounded-xl bg-linear-to-br shadow-sm"
        >
          <ShieldCheck class="size-5 text-white" />
        </div>
        <div class="flex-1">
          <h1 class="text-lg font-bold tracking-tight text-slate-900">Rôles & Droits</h1>
          <p class="text-sm text-slate-500">
            Configurez les permissions de chaque rôle —
            <span class="font-medium text-slate-700">{{ totalCaps }} capabilities disponibles</span>
          </p>
        </div>
        <CanGuard capability="ROLE_WRITE">
          <button
            type="button"
            class="bg-primary-600 hover:bg-primary-700 flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-semibold text-white shadow-sm transition-all"
            @click="drawerOpen = true"
          >
            <Plus class="size-4" />
            Nouveau rôle
          </button>
        </CanGuard>
      </div>
    </div>

    <!-- ── Contenu ── -->
    <div class="mx-auto max-w-4xl px-6 py-6">
      <!-- Erreur suppression -->
      <div
        v-if="deleteError"
        class="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
      >
        {{ deleteError }}
      </div>

      <!-- Loading -->
      <div v-if="roleStore.loading" class="flex flex-col items-center gap-3 py-20">
        <Loader2 class="size-8 animate-spin text-slate-300" />
        <p class="text-sm text-slate-400">Chargement des rôles…</p>
      </div>

      <template v-else>
        <!-- ── Capabilities ── -->
        <div class="mb-6 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div class="flex items-center justify-between border-b border-slate-100 px-5 py-3">
            <div class="flex items-center gap-2">
              <ShieldCheck class="size-4 text-slate-400" />
              <span class="text-sm font-semibold text-slate-700">Capabilities</span>
              <span
                class="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-500"
              >
                {{ totalCaps }}
              </span>
            </div>
          </div>
          <div class="px-5 py-4">
            <div
              v-for="(codes, prefix) in groupedCapabilities"
              :key="prefix"
              class="mb-4 last:mb-0"
            >
              <div class="mb-2 flex items-center gap-2">
                <component :is="catMeta(prefix).icon" class="size-3.5 text-slate-400" />
                <span class="text-[11px] font-bold tracking-widest text-slate-400 uppercase">
                  {{ catMeta(prefix).label || prefix }}
                </span>
              </div>
              <div class="flex flex-wrap gap-1.5">
                <span
                  v-for="code in codes"
                  :key="code"
                  class="inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-medium"
                  :class="catMeta(prefix).chipClass"
                >
                  {{ code }}
                </span>
              </div>
            </div>
            <p v-if="totalCaps === 0" class="text-sm text-slate-400">Aucune capability définie.</p>
          </div>
        </div>

        <!-- Liste des rôles -->
        <div class="space-y-3">
          <div
            v-for="role in roleStore.rolesWithPermissions"
            :key="role.id"
            class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition-shadow hover:shadow-md"
            :class="['border-l-4', roleMeta(role.libelle ?? '').borderClass]"
          >
            <!-- ── Header card ── -->
            <button
              type="button"
              class="flex w-full items-center gap-4 px-5 py-4 text-left"
              @click="toggle(role.id)"
            >
              <!-- Icône rôle -->
              <div
                class="flex size-10 shrink-0 items-center justify-center rounded-xl"
                :class="roleMeta(role.libelle ?? '').iconBgClass"
              >
                <component
                  :is="roleMeta(role.libelle ?? '').icon"
                  class="size-5"
                  :class="roleMeta(role.libelle ?? '').iconColorClass"
                />
              </div>

              <!-- Nom + description -->
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-2">
                  <span class="font-semibold text-slate-900">{{ role.libelle }}</span>
                  <!-- Dirty indicator -->
                  <span
                    v-if="isDirty(role.id)"
                    class="size-2 animate-pulse rounded-full bg-amber-400"
                    title="Modifications non enregistrées"
                  />
                  <!-- Saved indicator -->
                  <span
                    v-else-if="savedRoles.has(role.id)"
                    class="flex items-center gap-1 text-xs font-medium text-emerald-600"
                  >
                    <CheckCircle2 class="size-3.5" />
                    Enregistré
                  </span>
                </div>
                <p class="mt-0.5 text-xs text-slate-400">
                  {{ roleMeta(role.libelle ?? '').description }}
                </p>
              </div>

              <!-- Badge compteur + progress -->
              <div class="hidden shrink-0 items-center gap-3 sm:flex">
                <div class="text-right">
                  <div
                    class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1"
                    :class="roleMeta(role.libelle ?? '').badgeClass"
                  >
                    {{ selectedCount(role.id) }}/{{ totalCaps }}
                  </div>
                  <div class="mt-1.5 h-1 w-24 overflow-hidden rounded-full bg-slate-100">
                    <div
                      class="h-full rounded-full bg-current transition-all duration-300"
                      :class="roleMeta(role.libelle ?? '').iconColorClass"
                      :style="{ width: `${(selectedCount(role.id) / totalCaps) * 100}%` }"
                    />
                  </div>
                </div>
              </div>

              <ChevronDown
                class="size-4 shrink-0 text-slate-400 transition-transform duration-200"
                :class="openRole === role.id ? 'rotate-180' : ''"
              />
            </button>

            <!-- ── Corps accordéon ── -->
            <Transition
              enterActiveClass="transition-all duration-200 ease-out"
              enterFromClass="opacity-0 -translate-y-1"
              enterToClass="opacity-100 translate-y-0"
              leaveActiveClass="transition-all duration-150 ease-in"
              leaveFromClass="opacity-100 translate-y-0"
              leaveToClass="opacity-0 -translate-y-1"
            >
              <div v-if="openRole === role.id" class="border-t border-slate-100">
                <div class="px-5 py-5">
                  <!-- Catégories -->
                  <div
                    v-for="(codes, prefix) in groupedCapabilities"
                    :key="prefix"
                    class="mb-5 last:mb-0"
                  >
                    <!-- Header catégorie -->
                    <button
                      type="button"
                      class="mb-2.5 flex items-center gap-2 text-left"
                      :title="`Tout sélectionner / désélectionner — ${catMeta(prefix).label}`"
                      @click="toggleCategory(role.id, codes)"
                    >
                      <component :is="catMeta(prefix).icon" class="size-3.5 text-slate-400" />
                      <span class="text-[11px] font-bold tracking-widest text-slate-400 uppercase">
                        {{ catMeta(prefix).label || prefix }}
                      </span>
                      <span class="text-[10px] text-slate-300">
                        ({{ codes.filter((c) => isChecked(role.id, c)).length }}/{{ codes.length }})
                      </span>
                    </button>

                    <!-- Chips -->
                    <div class="flex flex-wrap gap-2">
                      <button
                        v-for="code in codes"
                        :key="code"
                        type="button"
                        class="inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition-all duration-150 focus:outline-none"
                        :class="
                          isChecked(role.id, code)
                            ? [catMeta(prefix).chipClass, catMeta(prefix).chipActiveClass]
                            : 'border-slate-200 bg-white text-slate-400 hover:border-slate-300 hover:text-slate-600'
                        "
                        @click="handleToggle(role.id, code)"
                      >
                        <Check v-if="isChecked(role.id, code)" class="size-3 shrink-0" />
                        <span v-else class="size-3 shrink-0 rounded-full border border-slate-200" />
                        {{ actionLabel(code) }}
                      </button>
                    </div>
                  </div>
                </div>

                <!-- ── Pied de carte ── -->
                <div
                  class="flex items-center justify-between border-t border-slate-100 bg-slate-50/60 px-5 py-3"
                >
                  <div class="flex items-center gap-2">
                    <span class="text-xs text-slate-400">
                      <span class="font-semibold text-slate-600">{{ selectedCount(role.id) }}</span>
                      permissions sélectionnées
                    </span>
                    <CanGuard capability="ROLE_WRITE">
                      <button
                        type="button"
                        class="flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-medium text-red-500 transition-colors hover:bg-red-50"
                        :title="`Supprimer le rôle ${role.libelle}`"
                        @click="confirmDeleteRole(role.id)"
                      >
                        <Trash2 class="size-3" />
                        Supprimer
                      </button>
                    </CanGuard>
                  </div>
                  <div class="flex items-center gap-2">
                    <button
                      v-if="isDirty(role.id)"
                      type="button"
                      class="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium text-slate-500 transition-colors hover:bg-slate-200"
                      @click="reset(role.id)"
                    >
                      <RotateCcw class="size-3" />
                      Annuler
                    </button>
                    <button
                      type="button"
                      :disabled="roleStore.saving"
                      class="flex items-center gap-1.5 rounded-lg px-4 py-1.5 text-xs font-semibold transition-all disabled:opacity-50"
                      :class="
                        savedRoles.has(role.id)
                          ? 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200'
                          : 'bg-primary-600 hover:bg-primary-700 text-white shadow-sm'
                      "
                      @click="save(role.id)"
                    >
                      <Loader2 v-if="roleStore.saving" class="size-3 animate-spin" />
                      <CheckCircle2 v-else-if="savedRoles.has(role.id)" class="size-3" />
                      <Check v-else class="size-3" />
                      {{ savedRoles.has(role.id) ? 'Enregistré' : 'Enregistrer' }}
                    </button>
                  </div>
                </div>
              </div>
            </Transition>
          </div>
        </div>
      </template>
    </div>

    <RoleDrawer :isOpen="drawerOpen" @close="drawerOpen = false" @created="drawerOpen = false" />
  </div>
</template>

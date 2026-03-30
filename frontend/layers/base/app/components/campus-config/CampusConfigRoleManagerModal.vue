<template>
  <AppDrawer
    :isOpen="isOpen"
    title="Gérer les rôles du ministère"
    initialSize="half"
    @close="emit('close')"
  >
    <!-- Corps -->
    <div v-if="isLoadingCatalog" class="flex items-center justify-center py-16">
      <Loader2 class="size-6 animate-spin text-slate-400" />
    </div>

    <div v-else-if="catalog.length === 0" class="py-16 text-center text-sm text-slate-400 italic">
      Aucun rôle dans le catalogue global.
    </div>

    <ul v-else class="space-y-4">
      <li
        v-for="item in catalog"
        :key="item.categorie_code"
        class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3"
      >
        <!-- En-tête catégorie -->
        <div class="mb-2 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="text-sm font-semibold text-slate-700">{{ item.categorie_libelle }}</span>
            <span
              class="rounded border border-slate-200 bg-white px-1.5 py-0.5 font-mono text-xs text-slate-400"
            >
              {{ item.categorie_code }}
            </span>
          </div>
          <button
            class="border-primary-200 bg-primary-50 text-primary-700 hover:bg-primary-100 flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-xs font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50"
            type="button"
            :disabled="isActivatingCategory === item.categorie_code"
            @click="handleActivateAll(item.categorie_code)"
          >
            <Loader2
              v-if="isActivatingCategory === item.categorie_code"
              class="size-3 animate-spin"
            />
            <CheckSquare v-else class="size-3" />
            Tout activer
          </button>
        </div>

        <!-- Liste des rôles -->
        <ul class="space-y-1.5">
          <li
            v-for="role in item.roles"
            :key="role.code"
            class="flex items-center justify-between rounded-lg bg-white px-3 py-2 shadow-sm"
          >
            <div class="min-w-0">
              <span class="text-sm font-medium text-slate-700">{{ role.libelle }}</span>
              <span class="ml-2 font-mono text-xs text-slate-400">{{ role.code }}</span>
            </div>

            <!-- Toggle switch -->
            <button
              class="relative ml-3 inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full transition-colors focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
              :class="isActive(role.code) ? 'bg-primary-600' : 'bg-slate-200'"
              type="button"
              :disabled="loadingRoles.has(role.code)"
              :aria-pressed="isActive(role.code)"
              :aria-label="
                isActive(role.code) ? `Désactiver ${role.libelle}` : `Activer ${role.libelle}`
              "
              @click="handleToggle(role.code)"
            >
              <span
                class="inline-block size-3.5 rounded-full bg-white shadow transition-transform"
                :class="isActive(role.code) ? 'translate-x-4' : 'translate-x-0.5'"
              />
              <Loader2
                v-if="loadingRoles.has(role.code)"
                class="absolute inset-0 m-auto size-3 animate-spin text-white"
              />
            </button>
          </li>

          <li v-if="item.roles.length === 0" class="py-1 text-xs text-slate-400 italic">
            Aucun rôle dans cette catégorie.
          </li>
        </ul>
      </li>
    </ul>
  </AppDrawer>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { CheckSquare, Loader2 } from 'lucide-vue-next'
import type { RolesByCategoryItem } from '~~/layers/base/types/role-competence'
import { useCampusConfig } from '../../composables/useCampusConfig'
import { useMLAConfirm } from '../../composables/useMLAConfirm'
import { RoleCompetenceRepository } from '../../repositories/RoleCompetenceRepository'

const props = defineProps<{
  ministereId: string
  isOpen: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

const campusConfig = useCampusConfig()
const { confirm } = useMLAConfirm()
const rcRepo = new RoleCompetenceRepository()

const catalog = ref<RolesByCategoryItem[]>([])
const activeRoleCodes = ref(new Set<string>())
const isLoadingCatalog = ref(false)
const loadingRoles = ref(new Set<string>())
const isActivatingCategory = ref<string | null>(null)

function isActive(roleCode: string): boolean {
  return activeRoleCodes.value.has(roleCode)
}

async function loadData(): Promise<void> {
  isLoadingCatalog.value = true
  try {
    await campusConfig.refreshActiveRolesForMinistere(props.ministereId)
    const [catalogItems] = await Promise.all([rcRepo.getByCategory()])
    catalog.value = catalogItems
    const active = campusConfig.activeRolesForMinistere(props.ministereId)
    activeRoleCodes.value = new Set(active.map((r) => r.code))
  } catch {
    // Erreur déjà notifiée par l'intercepteur
  } finally {
    isLoadingCatalog.value = false
  }
}

async function handleToggle(roleCode: string): Promise<void> {
  if (loadingRoles.value.has(roleCode)) return

  if (isActive(roleCode)) {
    const ok = await confirm('Désactiver ce rôle pour ce ministère ?')
    if (!ok) return
  }

  const next = new Set(loadingRoles.value)
  next.add(roleCode)
  loadingRoles.value = next

  try {
    if (isActive(roleCode)) {
      await campusConfig.deactivateRole(props.ministereId, roleCode)
      const updated = new Set(activeRoleCodes.value)
      updated.delete(roleCode)
      activeRoleCodes.value = updated
    } else {
      await campusConfig.activateRole(props.ministereId, roleCode)
      activeRoleCodes.value = new Set(activeRoleCodes.value).add(roleCode)
    }
  } catch {
    // Erreur déjà notifiée
  } finally {
    const done = new Set(loadingRoles.value)
    done.delete(roleCode)
    loadingRoles.value = done
  }
}

async function handleActivateAll(categorieCode: string): Promise<void> {
  isActivatingCategory.value = categorieCode
  try {
    await campusConfig.activateAllRolesForCategory(props.ministereId, categorieCode)
    const active = campusConfig.activeRolesForMinistere(props.ministereId)
    activeRoleCodes.value = new Set(active.map((r) => r.code))
  } catch {
    // Erreur déjà notifiée
  } finally {
    isActivatingCategory.value = null
  }
}

watch(
  () => props.isOpen,
  (open) => {
    if (open) loadData()
  },
  { immediate: true },
)
</script>

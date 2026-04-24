<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Building2, Plus, Pencil, Trash2, X } from 'lucide-vue-next'
import { useAuthStore } from '~~/layers/auth/app/stores/useAuthStore'
import type { OrganisationRead } from '~~/layers/base/types/organisation'
import type { CampusRead } from '~~/layers/base/types/campus'

definePageMeta({ layout: 'default' })

const authStore = useAuthStore()

if (!authStore.isSuperAdmin) {
  await navigateTo('/admin/profiles')
}

const {
  organisations,
  isFetching: isFetchingOrgs,
  create: createOrg,
  update: updateOrg,
  remove: removeOrg,
  refresh: refreshOrgs,
} = useOrganisations()
const {
  allCampuses,
  isFetching: isFetchingCampuses,
  create: createCampus,
  update: updateCampus,
  remove: removeCampus,
  refresh: refreshCampuses,
} = useCampusAdmin()
const { confirm } = useMLAConfirm()

onMounted(async () => {
  await Promise.all([refreshOrgs(), refreshCampuses()])
})

const TIMEZONES = [
  'Europe/Paris',
  'Africa/Abidjan',
  'Africa/Dakar',
  'America/New_York',
  'America/Toronto',
  'America/Montreal',
  'Europe/London',
  'Europe/Brussels',
]

// --- Organisation drawer state ---
const isOrgDrawerOpen = ref(false)
const editingOrg = ref<OrganisationRead | null>(null)
const isSubmittingOrg = ref(false)
const orgForm = ref({ nom: '', date_creation: '', parent_id: '' })

const openOrgCreate = () => {
  editingOrg.value = null
  orgForm.value = { nom: '', date_creation: '', parent_id: '' }
  isOrgDrawerOpen.value = true
}

const openOrgEdit = (org: OrganisationRead) => {
  editingOrg.value = org
  orgForm.value = {
    nom: org.nom,
    date_creation: org.date_creation,
    parent_id: org.parent_id ?? '',
  }
  isOrgDrawerOpen.value = true
}

const closeOrgDrawer = () => {
  isOrgDrawerOpen.value = false
  editingOrg.value = null
}

const handleOrgSubmit = async () => {
  isSubmittingOrg.value = true
  try {
    if (editingOrg.value) {
      await updateOrg(editingOrg.value.id, {
        nom: orgForm.value.nom,
        parent_id: orgForm.value.parent_id || null,
      })
    } else {
      await createOrg({
        nom: orgForm.value.nom,
        date_creation: orgForm.value.date_creation,
        parent_id: orgForm.value.parent_id || null,
      })
    }
    isOrgDrawerOpen.value = false
    editingOrg.value = null
  } catch {
    // errors handled by global fetch interceptor
  } finally {
    isSubmittingOrg.value = false
  }
}

const handleOrgDelete = async (org: OrganisationRead) => {
  const confirmed = await confirm(
    'Supprimer cette organisation ?',
    `L'organisation "${org.nom}" sera supprimée définitivement.`,
  )
  if (confirmed) await removeOrg(org.id)
}

const getOrgNom = (orgId: string): string => {
  return organisations.value.find((o) => o.id === orgId)?.nom ?? orgId
}

// --- Campus drawer state ---
const isCampusDrawerOpen = ref(false)
const editingCampus = ref<CampusRead | null>(null)
const isSubmittingCampus = ref(false)
const campusForm = ref({
  nom: '',
  ville: '',
  pays: 'France',
  timezone: 'Europe/Paris',
  organisation_id: '',
})

const openCampusCreate = () => {
  editingCampus.value = null
  campusForm.value = {
    nom: '',
    ville: '',
    pays: 'France',
    timezone: 'Europe/Paris',
    organisation_id: '',
  }
  isCampusDrawerOpen.value = true
}

const openCampusEdit = (campus: CampusRead) => {
  editingCampus.value = campus
  campusForm.value = {
    nom: campus.nom,
    ville: campus.ville,
    pays: campus.pays ?? 'France',
    timezone: campus.timezone,
    organisation_id: campus.organisation_id,
  }
  isCampusDrawerOpen.value = true
}

const closeCampusDrawer = () => {
  isCampusDrawerOpen.value = false
  editingCampus.value = null
}

const handleCampusSubmit = async () => {
  isSubmittingCampus.value = true
  try {
    if (editingCampus.value) {
      await updateCampus(editingCampus.value.id, {
        nom: campusForm.value.nom,
        ville: campusForm.value.ville,
        pays: campusForm.value.pays,
        timezone: campusForm.value.timezone,
        organisation_id: campusForm.value.organisation_id,
      })
    } else {
      await createCampus({
        nom: campusForm.value.nom,
        ville: campusForm.value.ville,
        pays: campusForm.value.pays,
        timezone: campusForm.value.timezone,
        organisation_id: campusForm.value.organisation_id,
      })
    }
    isCampusDrawerOpen.value = false
    editingCampus.value = null
  } catch {
    // errors handled by global fetch interceptor
  } finally {
    isSubmittingCampus.value = false
  }
}

const handleCampusDelete = async (campus: CampusRead) => {
  const confirmed = await confirm(
    'Supprimer ce campus ?',
    `Le campus "${campus.nom}" sera supprimé définitivement.`,
  )
  if (confirmed) await removeCampus(campus.id)
}
</script>

<template>
  <div class="mx-auto flex w-full max-w-5xl flex-col gap-6 p-4 md:p-8">
    <!-- En-tête -->
    <div class="flex items-center gap-3">
      <div class="flex size-10 items-center justify-center rounded-xl bg-(--color-primary-50)">
        <Building2 class="size-5 text-(--color-primary-700)" />
      </div>
      <div>
        <h1 class="text-xl font-bold text-slate-900">Campuses & Organisations</h1>
        <p class="mt-0.5 text-sm text-slate-500">
          Gérez la hiérarchie des organisations et les campus.
        </p>
      </div>
    </div>

    <!-- Section Organisations -->
    <section class="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div class="flex items-center justify-between border-b border-slate-100 px-6 py-4">
        <h2 class="text-base font-semibold text-slate-800">Organisations</h2>
        <button class="btn btn-primary btn-sm" :disabled="isFetchingOrgs" @click="openOrgCreate">
          <Plus class="size-4" />
          Nouvelle organisation
        </button>
      </div>

      <div class="px-6 py-4">
        <!-- Chargement -->
        <div v-if="isFetchingOrgs && organisations.length === 0" class="space-y-2">
          <div v-for="n in 2" :key="n" class="h-12 animate-pulse rounded-lg bg-slate-100" />
        </div>

        <div v-else-if="organisations.length === 0">
          <p class="text-sm text-slate-400 italic">
            Aucune organisation. Créez la première organisation.
          </p>
        </div>

        <ul v-else class="divide-y divide-slate-100">
          <li
            v-for="org in organisations"
            :key="org.id"
            class="flex items-center justify-between py-3"
          >
            <div class="flex items-center gap-3">
              <span class="text-sm font-medium text-slate-800">{{ org.nom }}</span>
              <span
                v-if="org.parent_id"
                class="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-500"
              >
                ↳ {{ getOrgNom(org.parent_id) }}
              </span>
              <span class="text-xs text-slate-400">{{ org.date_creation }}</span>
            </div>
            <div class="flex items-center gap-1">
              <button
                class="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
                title="Modifier"
                @click="openOrgEdit(org)"
              >
                <Pencil class="size-4" />
              </button>
              <button
                class="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-600"
                title="Supprimer"
                @click="handleOrgDelete(org)"
              >
                <Trash2 class="size-4" />
              </button>
            </div>
          </li>
        </ul>
      </div>
    </section>

    <!-- Section Campuses -->
    <section class="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div class="flex items-center justify-between border-b border-slate-100 px-6 py-4">
        <h2 class="text-base font-semibold text-slate-800">Campuses</h2>
        <button
          class="btn btn-primary btn-sm"
          :disabled="isFetchingCampuses"
          @click="openCampusCreate"
        >
          <Plus class="size-4" />
          Nouveau campus
        </button>
      </div>

      <div class="px-6 py-4">
        <!-- État chargement -->
        <div v-if="isFetchingCampuses && allCampuses.length === 0" class="space-y-2">
          <div v-for="n in 3" :key="n" class="h-16 animate-pulse rounded-xl bg-slate-100" />
        </div>

        <!-- État vide -->
        <div
          v-else-if="allCampuses.length === 0"
          class="flex flex-col items-center gap-3 py-10 text-center"
        >
          <div class="flex size-14 items-center justify-center rounded-2xl bg-slate-100">
            <Building2 class="size-7 text-slate-400" />
          </div>
          <div>
            <p class="text-sm font-medium text-slate-700">Aucun campus pour l'instant</p>
            <p class="mt-0.5 text-xs text-slate-400">
              Créez le premier campus pour démarrer la configuration.
            </p>
          </div>
          <button class="btn btn-primary mt-1" @click="openCampusCreate">
            <Plus class="size-4" />
            Créer un campus
          </button>
        </div>

        <!-- Liste campuses -->
        <div v-else class="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div
            v-for="campus in allCampuses"
            :key="campus.id"
            class="flex items-start justify-between rounded-xl border border-slate-100 bg-slate-50 p-4"
          >
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-semibold text-slate-800">{{ campus.nom }}</p>
              <p class="mt-0.5 text-xs text-slate-500">
                {{ campus.ville }}<span v-if="campus.pays">, {{ campus.pays }}</span>
              </p>
              <div class="mt-2 flex flex-wrap gap-1.5">
                <span class="rounded-full bg-slate-200 px-2 py-0.5 text-xs text-slate-600">
                  {{ campus.timezone }}
                </span>
                <span
                  class="rounded-full bg-(--color-primary-50) px-2 py-0.5 text-xs text-(--color-primary-700)"
                >
                  {{ getOrgNom(campus.organisation_id) }}
                </span>
              </div>
            </div>
            <div class="ml-2 flex shrink-0 items-center gap-1">
              <button
                class="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-white hover:text-slate-700"
                title="Modifier"
                @click="openCampusEdit(campus)"
              >
                <Pencil class="size-4" />
              </button>
              <button
                class="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-600"
                title="Supprimer"
                @click="handleCampusDelete(campus)"
              >
                <Trash2 class="size-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Drawer Organisation -->
    <Teleport to="body">
      <Transition name="drawer-fade">
        <div v-if="isOrgDrawerOpen" class="fixed inset-0 z-50 flex justify-end">
          <div class="absolute inset-0 bg-slate-900/30 backdrop-blur-sm" @click="closeOrgDrawer" />
          <div class="relative z-10 flex h-full w-full max-w-md flex-col bg-white shadow-2xl">
            <div class="flex items-center justify-between border-b border-slate-100 px-6 py-5">
              <h2 class="text-base font-semibold text-slate-900">
                {{ editingOrg ? "Modifier l'organisation" : 'Nouvelle organisation' }}
              </h2>
              <button
                class="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
                @click="closeOrgDrawer"
              >
                <X class="size-5" />
              </button>
            </div>

            <div class="flex-1 overflow-y-auto px-6 py-6">
              <div class="space-y-4">
                <div>
                  <label class="mb-1 block text-sm font-medium text-slate-700">
                    Nom <span class="text-red-500">*</span>
                  </label>
                  <input
                    v-model="orgForm.nom"
                    type="text"
                    placeholder="Ex: ICC Occitanie"
                    class="form-input"
                  />
                </div>

                <div v-if="!editingOrg">
                  <label class="mb-1 block text-sm font-medium text-slate-700">
                    Date de création <span class="text-red-500">*</span>
                  </label>
                  <input v-model="orgForm.date_creation" type="date" class="form-input" />
                </div>

                <div>
                  <label class="mb-1 block text-sm font-medium text-slate-700">
                    Organisation mère
                  </label>
                  <div class="form-select-wrapper">
                    <select v-model="orgForm.parent_id" class="form-input form-select">
                      <option value="">Aucune</option>
                      <option
                        v-for="org in organisations.filter((o) => o.id !== editingOrg?.id)"
                        :key="org.id"
                        :value="org.id"
                      >
                        {{ org.nom }}
                      </option>
                    </select>
                    <svg
                      class="form-select-chevron"
                      viewBox="0 0 14 14"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                    >
                      <path d="M3 5l4 4 4-4" />
                    </svg>
                  </div>
                </div>
              </div>
            </div>

            <div class="border-t border-slate-100 px-6 py-4">
              <div class="flex justify-end gap-3">
                <button class="btn btn-secondary" @click="closeOrgDrawer">Annuler</button>
                <button
                  class="btn btn-primary"
                  :disabled="
                    isSubmittingOrg ||
                    !orgForm.nom.trim() ||
                    (!editingOrg && !orgForm.date_creation)
                  "
                  @click="handleOrgSubmit"
                >
                  Enregistrer
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Drawer Campus -->
    <Teleport to="body">
      <Transition name="drawer-fade">
        <div v-if="isCampusDrawerOpen" class="fixed inset-0 z-50 flex justify-end">
          <!-- Overlay -->
          <div
            class="absolute inset-0 bg-slate-900/30 backdrop-blur-sm"
            @click="closeCampusDrawer"
          />

          <!-- Panel -->
          <div class="relative z-10 flex h-full w-full max-w-md flex-col bg-white shadow-2xl">
            <!-- Drawer header -->
            <div class="flex items-center justify-between border-b border-slate-100 px-6 py-5">
              <h2 class="text-base font-semibold text-slate-900">
                {{ editingCampus ? 'Modifier le campus' : 'Nouveau campus' }}
              </h2>
              <button
                class="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
                @click="closeCampusDrawer"
              >
                <X class="size-5" />
              </button>
            </div>

            <!-- Drawer body -->
            <div class="flex-1 overflow-y-auto px-6 py-6">
              <div class="space-y-4">
                <div>
                  <label class="mb-1 block text-sm font-medium text-slate-700">
                    Nom du campus <span class="text-red-500">*</span>
                  </label>
                  <input
                    v-model="campusForm.nom"
                    type="text"
                    placeholder="Ex: Campus Cugnaux"
                    class="form-input"
                  />
                </div>

                <div>
                  <label class="mb-1 block text-sm font-medium text-slate-700">
                    Ville <span class="text-red-500">*</span>
                  </label>
                  <input
                    v-model="campusForm.ville"
                    type="text"
                    placeholder="Ex: Cugnaux"
                    class="form-input"
                  />
                </div>

                <div>
                  <label class="mb-1 block text-sm font-medium text-slate-700">Pays</label>
                  <input
                    v-model="campusForm.pays"
                    type="text"
                    placeholder="Ex: France"
                    class="form-input"
                  />
                </div>

                <div>
                  <label class="mb-1 block text-sm font-medium text-slate-700">
                    Fuseau horaire
                  </label>
                  <div class="form-select-wrapper">
                    <select v-model="campusForm.timezone" class="form-input form-select">
                      <option v-for="tz in TIMEZONES" :key="tz" :value="tz">{{ tz }}</option>
                    </select>
                    <svg
                      class="form-select-chevron"
                      viewBox="0 0 14 14"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                    >
                      <path d="M3 5l4 4 4-4" />
                    </svg>
                  </div>
                </div>

                <div>
                  <label class="mb-1 block text-sm font-medium text-slate-700">
                    Organisation <span class="text-red-500">*</span>
                  </label>
                  <div class="form-select-wrapper">
                    <select v-model="campusForm.organisation_id" class="form-input form-select">
                      <option value="" disabled>Sélectionner une organisation</option>
                      <option v-for="org in organisations" :key="org.id" :value="org.id">
                        {{ org.nom }}
                      </option>
                    </select>
                    <svg
                      class="form-select-chevron"
                      viewBox="0 0 14 14"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                    >
                      <path d="M3 5l4 4 4-4" />
                    </svg>
                  </div>
                </div>
              </div>
            </div>

            <!-- Drawer footer -->
            <div class="border-t border-slate-100 px-6 py-4">
              <div class="flex justify-end gap-3">
                <button class="btn btn-secondary" @click="closeCampusDrawer">Annuler</button>
                <button
                  class="btn btn-primary"
                  :disabled="
                    isSubmittingCampus || !campusForm.nom.trim() || !campusForm.organisation_id
                  "
                  @click="handleCampusSubmit"
                >
                  Enregistrer
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
@reference "../../assets/css/main.css";

.drawer-fade-enter-active,
.drawer-fade-leave-active {
  transition: opacity 0.25s ease;
}
.drawer-fade-enter-active .relative,
.drawer-fade-leave-active .relative {
  transition: transform 0.25s ease;
}
.drawer-fade-enter-from,
.drawer-fade-leave-to {
  opacity: 0;
}
</style>

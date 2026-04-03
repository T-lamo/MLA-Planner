<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { refDebounced } from '@vueuse/core'
import { Search, X } from 'lucide-vue-next'
import ProfileHeader from '../../components/profile/ProfileHeader.vue'
import ProfileCard from '../../components/profile/ProfileCard.vue'
import ProfileFormDrawer from '../../components/profile/ProfileFormDrawer.vue'
import AppSelect from '../../components/ui/AppSelect.vue'
import AppPagination from '../../components/ui/AppPagination.vue'
import CanGuard from '../../components/ui/CanGuard.vue'
import { usePagination } from '../../stores/utils/usePagination'

import type {
  ProfilReadFull,
  ProfilCreateFull,
  ProfilUpdateFull,
} from '~~/layers/base/types/profiles'
import type { CampusRead } from '~~/layers/base/types/campus'
import { ProfileRepository } from '~~/layers/base/app/repositories/ProfileRepository'
import { useAuthStore } from '~~/layers/auth/app/stores/useAuthStore'
import { useProfileStore } from '~~/layers/base/app/stores/useProfileStore'

const authStore = useAuthStore()
const profileStore = useProfileStore()

const { profiles, isFetching, totalProfiles, activeCampusId, campuses, create, update, remove } =
  useProfiles()

// Tous les campus pour le formulaire
const allCampuses = ref<CampusRead[]>([])
onMounted(async () => {
  try {
    allCampuses.value = await new ProfileRepository().getAllCampuses()
  } catch {
    allCampuses.value = campuses.value
  }
})

const { ministeresByCampus, fetchDetailedMinisteres } = useCampuses()

// ── Filtre ministère ───────────────────────────────────────────────
// '' = vue campus (tous), sinon ID du ministère sélectionné
const selectedMinistereId = ref('')

// Pagination locale pour la vue ministère (mémoire, 50 items/page)
const {
  pagination: ministrePag,
  total: ministreTotal,
  currentPage: ministreCurrentPage,
  totalPages: ministreTotalPages,
  setTotal: ministreSetTotal,
  goToPage: ministreGoToPage,
  resetPagination: ministreResetPagination,
} = usePagination(20)

// Toujours basé sur les ministères de l'utilisateur — admin ou pas
const ministeresOptions = computed(() => [
  { label: 'Tous les membres', value: '' },
  ...profileStore.myMinisteres.map((m) => ({ label: m.nom, value: m.id })),
])

// Afficher le sélecteur seulement si au moins un ministère disponible
const showMinistereFilter = computed(() => ministeresOptions.value.length > 1)

// ── Recherche avec debounce 300ms ──────────────────────────────────
const searchInput = ref('')
const searchQuery = refDebounced(searchInput, 300)

// ── Chargement des données au changement de campus ─────────────────
watch(
  activeCampusId,
  async (newId) => {
    if (!newId) return
    // Invalider le cache ministère — les profils appartiennent à l'ancien campus
    profileStore.clearMinistereCache()
    selectedMinistereId.value = ''
    fetchDetailedMinisteres(newId)
    if (authStore.canReadMembres) {
      await profileStore.fetchMyMinisteres(newId)
    }
  },
  { immediate: true },
)

// Charger les profils du ministère sélectionné (cache par campus+ministère)
watch(selectedMinistereId, async (id) => {
  ministreResetPagination()
  if (!id || !activeCampusId.value) return
  const cacheKey = `${activeCampusId.value}:${id}`
  if (!(cacheKey in profileStore.profilesByMinistere)) {
    await profileStore.fetchProfilesByMinistere(id, activeCampusId.value)
  }
})

// ── Profils filtrés ────────────────────────────────────────────────
function filterBySearch(list: ProfilReadFull[]): ProfilReadFull[] {
  const q = searchQuery.value.toLowerCase().trim()
  if (!q) return list
  return list.filter(
    (p) =>
      p.nom.toLowerCase().includes(q) ||
      p.prenom.toLowerCase().includes(q) ||
      p.email.toLowerCase().includes(q),
  )
}

const campusProfiles = computed(() => filterBySearch(profiles.value))

const allMinistereProfiles = computed<ProfilReadFull[]>(() => {
  if (!selectedMinistereId.value || !activeCampusId.value) return []
  const cacheKey = `${activeCampusId.value}:${selectedMinistereId.value}`
  return filterBySearch(profileStore.profilesByMinistere[cacheKey] ?? [])
})

// Slice paginé pour la vue ministère
const ministereProfiles = computed<ProfilReadFull[]>(() => {
  ministreSetTotal(allMinistereProfiles.value.length)
  return allMinistereProfiles.value.slice(
    ministrePag.offset,
    ministrePag.offset + ministrePag.limit,
  )
})

const displayedProfiles = computed(() =>
  selectedMinistereId.value ? ministereProfiles.value : campusProfiles.value,
)

const displayedTotal = computed(() =>
  selectedMinistereId.value ? allMinistereProfiles.value.length : totalProfiles.value,
)

const isListLoading = computed(() =>
  selectedMinistereId.value ? profileStore.loadingMinistere : isFetching.value,
)

// Label contextuel pour le header
const contextLabel = computed(() => {
  if (!activeCampusId.value) return undefined
  if (selectedMinistereId.value) {
    const found = ministeresOptions.value.find((o) => o.value === selectedMinistereId.value)
    return found?.label
  }
  const campus = campuses.value.find((c) => c.id === activeCampusId.value)
  return campus?.nom ?? undefined
})

// ── CRUD ──────────────────────────────────────────────────────────
const isDrawerOpen = ref(false)
const isSubmitting = ref(false)
const editingProfile = ref<ProfilReadFull | null>(null)

const handleOpenCreate = () => {
  editingProfile.value = null
  isDrawerOpen.value = true
}

const handleOpenEdit = (profile: ProfilReadFull) => {
  editingProfile.value = profile
  isDrawerOpen.value = true
}

const handleFormSubmit = async (formData: ProfilCreateFull) => {
  isSubmitting.value = true
  try {
    if (editingProfile.value) {
      const updatePayload: ProfilUpdateFull = {
        nom: formData.nom,
        prenom: formData.prenom,
        email: formData.email,
        telephone: formData.telephone,
        actif: formData.actif,
        campus_ids: formData.campus_ids,
        campus_principal_id: formData.campus_principal_id ?? null,
        ministere_ids: formData.ministere_ids,
        pole_ids: formData.pole_ids,
        role_codes: formData.role_codes,
      }
      if (formData.utilisateur) {
        updatePayload.utilisateur = {
          username: formData.utilisateur.username,
          actif: formData.utilisateur.actif,
        }
        if (formData.utilisateur.password) {
          updatePayload.utilisateur.password = formData.utilisateur.password
        }
        if (formData.utilisateur.roles_ids?.length) {
          updatePayload.utilisateur.roles_ids = formData.utilisateur.roles_ids
        }
      }
      await update(editingProfile.value.id, updatePayload)
    } else {
      const createPayload: ProfilCreateFull = {
        ...formData,
        utilisateur: formData.utilisateur
          ? { ...formData.utilisateur, password: formData.utilisateur.password || undefined }
          : formData.utilisateur,
      }
      await create(createPayload)
    }
    isDrawerOpen.value = false
  } catch {
    // errors handled globally
  } finally {
    isSubmitting.value = false
  }
}

const handleDelete = async (id: string) => {
  if (confirm('Êtes-vous sûr de vouloir supprimer ce profil ?')) {
    await remove(id)
  }
}
</script>

<template>
  <div class="mx-auto flex w-full max-w-7xl flex-col gap-6 p-4 md:p-8">
    <!-- Accès refusé -->
    <div
      v-if="!authStore.canReadMembres"
      class="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700"
    >
      Vous n'avez pas les droits nécessaires pour consulter les profils membres.
    </div>

    <template v-else>
      <!-- En-tête -->
      <ProfileHeader
        :total="displayedTotal"
        :isFetching="isListLoading"
        :contextLabel="contextLabel"
        @add="handleOpenCreate"
      />

      <!-- Barre de contrôle : recherche + filtre ministère -->
      <div
        class="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:flex-row sm:items-center"
      >
        <!-- Recherche -->
        <div class="relative flex-1">
          <Search
            class="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-slate-400"
          />
          <input
            v-model="searchInput"
            type="text"
            placeholder="Rechercher par nom, prénom, email…"
            class="form-input w-full bg-white pr-8 pl-10"
          />
          <button
            v-if="searchInput"
            class="absolute top-1/2 right-2.5 -translate-y-1/2 rounded p-0.5 text-slate-400 transition-colors hover:text-slate-700"
            type="button"
            aria-label="Effacer la recherche"
            @click="searchInput = ''"
          >
            <X class="size-3.5" />
          </button>
        </div>

        <!-- Filtre ministère -->
        <div v-if="showMinistereFilter" class="flex items-center gap-3">
          <span class="text-xs font-bold tracking-wider whitespace-nowrap text-slate-400 uppercase">
            Ministère
          </span>
          <AppSelect v-model="selectedMinistereId" :options="ministeresOptions" class="min-w-44" />
        </div>
      </div>

      <!-- Avertissement campus manquant -->
      <div
        v-if="campuses.length === 0 && !isListLoading"
        class="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-700"
      >
        Aucun campus disponible.
        <template v-if="authStore.isSuperAdmin">
          <RouterLink to="/admin/campuses" class="font-medium underline">
            Créer le premier campus
          </RouterLink>
        </template>
        <template v-else> Contactez un Super Admin pour créer un campus. </template>
      </div>

      <!-- Skeleton chargement -->
      <div v-if="isListLoading" class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <div v-for="n in 6" :key="n" class="h-24 animate-pulse rounded-xl bg-slate-100" />
      </div>

      <!-- Liste -->
      <template v-else>
        <!-- État vide contextualisé -->
        <div
          v-if="displayedProfiles.length === 0"
          class="flex flex-col items-center gap-3 rounded-xl border border-dashed border-slate-200 py-14 text-center"
        >
          <template v-if="searchInput">
            <p class="text-sm font-medium text-slate-600">
              Aucun résultat pour
              <span class="font-semibold">"{{ searchInput }}"</span>
            </p>
            <button
              class="text-xs text-(--color-primary-600) underline hover:no-underline"
              @click="searchInput = ''"
            >
              Effacer la recherche
            </button>
          </template>
          <template v-else>
            <p class="text-sm text-slate-500">Aucun membre dans cette vue.</p>
            <CanGuard capability="MEMBRE_CREATE">
              <button class="btn btn-primary btn-sm" @click="handleOpenCreate">
                Ajouter le premier membre
              </button>
            </CanGuard>
          </template>
        </div>

        <TransitionGroup
          v-else
          name="profile-list"
          tag="div"
          class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3"
        >
          <ProfileCard
            v-for="profile in displayedProfiles"
            :key="profile.id"
            :profile="profile"
            @edit="handleOpenEdit"
            @delete="handleDelete"
          />
        </TransitionGroup>

        <!-- Pagination vue campus (serveur) -->
        <AppPagination
          v-if="!selectedMinistereId"
          :currentPage="profileStore.currentPage"
          :totalPages="profileStore.totalPages"
          :total="profileStore.total"
          :loading="isFetching"
          @change="
            (page) => {
              profileStore.goToPage(page)
              profileStore.fetchProfiles()
            }
          "
        />

        <!-- Pagination vue ministère (client) -->
        <AppPagination
          v-else
          :currentPage="ministreCurrentPage"
          :totalPages="ministreTotalPages"
          :total="ministreTotal"
          :loading="profileStore.loadingMinistere"
          @change="(page) => ministreGoToPage(page)"
        />
      </template>

      <ProfileFormDrawer
        :isOpen="isDrawerOpen"
        :editingProfile="editingProfile"
        :campuses="allCampuses"
        :prefillCampusId="editingProfile ? undefined : activeCampusId"
        :ministeresDetailed="ministeresByCampus"
        :isSubmitting="isSubmitting"
        @close="isDrawerOpen = false"
        @submit="handleFormSubmit"
      />
    </template>
  </div>
</template>

<style scoped>
@reference "../../assets/css/main.css";

.profile-list-enter-active,
.profile-list-leave-active {
  transition: all 0.25s ease;
}
.profile-list-enter-from,
.profile-list-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
.profile-list-move {
  transition: transform 0.25s ease;
}
</style>

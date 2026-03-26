<script setup lang="ts">
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'
import {
  User,
  Mail,
  Phone,
  MapPin,
  ShieldCheck,
  Lock,
  Building2,
  Check,
  Minus,
  Search,
  ChevronDown,
  X,
} from 'lucide-vue-next'
import type {
  ProfilCreateFull,
  ProfilReadFull,
  ProfilUpdateFull,
} from '~~/layers/base/types/profiles'
import type { CampusRead } from '~~/layers/base/types/campus'
import type { MinistereReadWithRelations } from '~~/layers/base/types/ministere'

interface Props {
  isOpen: boolean
  editingProfile: ProfilReadFull | null
  campuses: CampusRead[]
  ministeresDetailed: MinistereReadWithRelations[]
  isSubmitting: boolean
  isLoadingReferences?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'submit', data: ProfilCreateFull | ProfilUpdateFull): void
}>()

// --- ÉTATS ---
const showUserAccount = ref(false)
const campusSearch = ref('')
const ministereSearch = ref('')
const openMinisteres = ref<Set<string>>(new Set())
const showCampusDropdown = ref(false)
const campusContainerRef = ref<HTMLElement | null>(null)

const form = ref<ProfilCreateFull>({
  nom: '',
  prenom: '',
  email: '',
  telephone: '',
  actif: true,
  campus_ids: [],
  ministere_ids: [],
  pole_ids: [],
  utilisateur: undefined,
})

// --- LOGIQUE CLICK OUTSIDE (CAMPUS) ---
const handleClickOutside = (event: MouseEvent) => {
  if (campusContainerRef.value && !campusContainerRef.value.contains(event.target as Node)) {
    showCampusDropdown.value = false
  }
}

onMounted(() => document.addEventListener('mousedown', handleClickOutside))
onUnmounted(() => document.removeEventListener('mousedown', handleClickOutside))

// --- WATCHERS & RESET ---
const resetForm = () => {
  form.value = {
    nom: '',
    prenom: '',
    email: '',
    telephone: '',
    actif: true,
    campus_ids: [],
    ministere_ids: [],
    pole_ids: [],
    utilisateur: undefined,
  }
  showUserAccount.value = false
  openMinisteres.value.clear()
}

watch(
  () => props.isOpen,
  (open) => {
    if (!open) return
    if (props.editingProfile) {
      const p = props.editingProfile
      const mIds = new Set(p.ministeres?.map((m) => m.id) || [])
      const pIds = p.poles?.map((pole) => pole.id) || []
      p.poles?.forEach((pole) => {
        if (pole.ministere_id) mIds.add(pole.ministere_id)
      })

      form.value = {
        nom: p.nom,
        prenom: p.prenom,
        email: p.email,
        telephone: p.telephone || '',
        actif: p.actif,
        campus_ids: p.campuses?.map((c) => c.id) || [],
        ministere_ids: Array.from(mIds),
        pole_ids: pIds,
        utilisateur: p.utilisateur
          ? { username: p.utilisateur.username, actif: p.utilisateur.actif, roles_ids: [] }
          : undefined,
      }
      showUserAccount.value = !!p.utilisateur
    } else {
      resetForm()
    }
  },
  { immediate: true },
)

// --- LOGIQUE MINISTÈRES & PÔLES ---
const handleToggleMinistere = (min: MinistereReadWithRelations) => {
  const currentMIds = new Set(form.value.ministere_ids)
  const currentPIds = new Set(form.value.pole_ids)
  const childIds = min.poles.map((p) => p.id)

  if (currentMIds.has(min.id)) {
    currentMIds.delete(min.id)
    childIds.forEach((id) => currentPIds.delete(id))
  } else {
    currentMIds.add(min.id)
    childIds.forEach((id) => currentPIds.add(id))
  }
  form.value.ministere_ids = Array.from(currentMIds)
  form.value.pole_ids = Array.from(currentPIds)
}

const handleTogglePole = (ministereId: string, poleId: string) => {
  const currentPIds = new Set(form.value.pole_ids)
  const currentMIds = new Set(form.value.ministere_ids)

  if (currentPIds.has(poleId)) {
    currentPIds.delete(poleId)
  } else {
    currentPIds.add(poleId)
  }

  const min = props.ministeresDetailed.find((m) => m.id === ministereId)
  if (min) {
    const hasAnyPole = min.poles.some((p) => currentPIds.has(p.id))
    if (hasAnyPole) {
      currentMIds.add(ministereId)
    } else {
      currentMIds.delete(ministereId)
    }
  }

  form.value.pole_ids = Array.from(currentPIds)
  form.value.ministere_ids = Array.from(currentMIds)
}

const getMinistereState = (min: MinistereReadWithRelations) => {
  const isSelected = form.value.ministere_ids.includes(min.id)
  const childIds = min.poles.map((p) => p.id)
  const selectedCount = childIds.filter((id) => form.value.pole_ids.includes(id)).length
  return {
    isSelected,
    isIndeterminate: isSelected && selectedCount > 0 && selectedCount < childIds.length,
    isAllSelected: childIds.length > 0 && selectedCount === childIds.length,
    selectedCount,
    totalPoles: childIds.length,
  }
}

// --- FILTRAGE COMPUTED ---
const filteredCampuses = computed(() =>
  campusSearch.value
    ? props.campuses.filter((c) => c.nom.toLowerCase().includes(campusSearch.value.toLowerCase()))
    : props.campuses,
)

const filteredMinisteres = computed(() => {
  if (!ministereSearch.value) return props.ministeresDetailed
  const s = ministereSearch.value.toLowerCase()
  return props.ministeresDetailed.filter(
    (m) => m.nom.toLowerCase().includes(s) || m.poles.some((p) => p.nom.toLowerCase().includes(s)),
  )
})

const toggleCampus = (id: string) => {
  const idx = form.value.campus_ids.indexOf(id)
  if (idx > -1) {
    form.value.campus_ids.splice(idx, 1)
  } else {
    form.value.campus_ids.push(id)
  }
}

const toggleAccordion = (id: string) => {
  if (openMinisteres.value.has(id)) {
    openMinisteres.value.delete(id)
  } else {
    openMinisteres.value.add(id)
  }
}

const handleSubmit = () => {
  const payload = JSON.parse(JSON.stringify(form.value))
  if (!showUserAccount.value) delete payload.utilisateur
  emit('submit', payload)
}
</script>

<template>
  <AppDrawer
    :isOpen="isOpen"
    :title="editingProfile ? 'Édition du Profil' : 'Nouveau Collaborateur'"
    initialSize="half"
    @close="emit('close')"
  >
    <form id="profileForm" class="space-y-8 pb-10" @submit.prevent="handleSubmit">
      <section class="space-y-4">
        <header class="section-header">
          <User class="size-3.5" /><span>Informations Personnelles</span>
        </header>
        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div class="form-group">
            <label>Nom</label
            ><input
              v-model="form.nom"
              type="text"
              required
              class="input-field"
              placeholder="Ex: MARTIN"
            />
          </div>
          <div class="form-group">
            <label>Prénom</label
            ><input
              v-model="form.prenom"
              type="text"
              required
              class="input-field"
              placeholder="Ex: Lucas"
            />
          </div>
          <div class="form-group">
            <label>Email</label>
            <div class="input-wrapper">
              <Mail class="input-icon" /><input
                v-model="form.email"
                type="email"
                required
                class="input-field with-icon"
              />
            </div>
          </div>
          <div class="form-group">
            <label>Téléphone</label>
            <div class="input-wrapper">
              <Phone class="input-icon" /><input
                v-model="form.telephone"
                type="tel"
                class="input-field with-icon"
              />
            </div>
          </div>
        </div>
        <div class="status-toggle-card group cursor-pointer" @click="form.actif = !form.actif">
          <div class="flex flex-col">
            <span class="text-xs font-bold text-slate-700">Disponibilité</span
            ><span class="text-[11px] text-slate-500">Visible dans l'annuaire</span>
          </div>
          <button type="button" :class="['toggle-pill', form.actif ? 'active' : '']">
            <span :class="['toggle-circle', form.actif ? 'translate-x-5' : 'translate-x-0']"></span>
          </button>
        </div>
      </section>

      <section class="space-y-4">
        <header class="section-header sticky top-0 z-10 bg-white py-2">
          <MapPin class="size-3.5" /><span>Affectation Campus</span>
        </header>
        <div ref="campusContainerRef" class="space-y-3">
          <div v-if="form.campus_ids.length > 0" class="flex flex-wrap gap-2">
            <span v-for="cId in form.campus_ids.slice(0, 5)" :key="cId" class="campus-tag">
              {{ campuses.find((c) => c.id === cId)?.nom }}
              <X class="size-3 cursor-pointer hover:text-red-500" @click.stop="toggleCampus(cId)" />
            </span>
            <span v-if="form.campus_ids.length > 5" class="campus-tag-more"
              >+{{ form.campus_ids.length - 5 }}</span
            >
          </div>
          <div class="relative">
            <div class="input-wrapper">
              <Search class="input-icon" />
              <input
                v-model="campusSearch"
                type="text"
                class="input-field with-icon"
                placeholder="Rechercher un campus..."
                @focus="showCampusDropdown = true"
              />
            </div>
            <div
              v-if="showCampusDropdown && filteredCampuses.length > 0"
              class="custom-scrollbar absolute z-50 mt-1 max-h-48 w-full overflow-y-auto rounded-xl border border-slate-200 bg-white shadow-xl"
            >
              <div
                v-for="c in filteredCampuses"
                :key="c.id"
                class="flex cursor-pointer items-center justify-between px-4 py-2 text-sm hover:bg-slate-50"
                @click="toggleCampus(c.id)"
              >
                <span :class="form.campus_ids.includes(c.id) ? 'text-primary-600 font-bold' : ''">{{
                  c.nom
                }}</span>
                <Check v-if="form.campus_ids.includes(c.id)" class="text-primary-600 size-4" />
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="space-y-4">
        <header class="section-header sticky top-0 z-10 bg-white py-2">
          <Building2 class="size-3.5" /><span>Ministères & Pôles</span>
        </header>
        <div class="input-wrapper mb-4">
          <Search class="input-icon" /><input
            v-model="ministereSearch"
            type="text"
            class="input-field with-icon"
            placeholder="Filtrer..."
          />
        </div>

        <div class="space-y-3">
          <div
            v-for="min in filteredMinisteres"
            :key="min.id"
            class="ministere-accordion"
            :class="{ 'is-active': getMinistereState(min).isSelected }"
          >
            <div class="flex items-center justify-between p-3" @click="toggleAccordion(min.id)">
              <div class="flex items-center gap-3">
                <div
                  :class="[
                    'flex size-5 shrink-0 items-center justify-center rounded-md border transition-all',
                    getMinistereState(min).isSelected
                      ? 'bg-primary-600 border-primary-600'
                      : 'border-slate-200 bg-white',
                  ]"
                  @click.stop="handleToggleMinistere(min)"
                >
                  <Check v-if="getMinistereState(min).isAllSelected" class="size-3.5 text-white" />
                  <Minus
                    v-else-if="getMinistereState(min).isIndeterminate"
                    class="size-3.5 text-white"
                  />
                </div>

                <div>
                  <h4 class="mb-1 text-sm leading-none font-bold text-slate-700">{{ min.nom }}</h4>
                  <div class="flex items-center gap-1.5">
                    <span
                      v-if="getMinistereState(min).selectedCount > 0"
                      class="text-primary-600 text-[10px] font-bold"
                    >
                      {{ getMinistereState(min).selectedCount }} /
                      {{ getMinistereState(min).totalPoles }} pôles sélectionnés
                    </span>
                    <span v-else class="text-[10px] font-medium text-slate-400">
                      {{ getMinistereState(min).totalPoles }} pôles disponibles
                    </span>
                  </div>
                </div>
              </div>

              <div class="flex items-center gap-3">
                <button
                  type="button"
                  class="text-primary-600 hover:text-primary-700 bg-primary-50 rounded px-2 py-1 text-[10px] font-black tracking-tighter uppercase"
                  @click.stop="handleToggleMinistere(min)"
                >
                  {{ getMinistereState(min).isAllSelected ? 'Tout vider' : 'Tout cocher' }}
                </button>
                <ChevronDown
                  :class="[
                    'size-4 text-slate-400 transition-transform duration-300',
                    openMinisteres.has(min.id) ? 'rotate-180' : '',
                  ]"
                />
              </div>
            </div>

            <Transition name="form-expand">
              <div
                v-show="openMinisteres.has(min.id) || ministereSearch"
                class="border-t border-slate-100 bg-slate-50/50 p-3"
              >
                <div class="grid grid-cols-2 gap-2 sm:grid-cols-3">
                  <button
                    v-for="pole in min.poles"
                    :key="pole.id"
                    type="button"
                    :class="['pole-pill', form.pole_ids.includes(pole.id) ? 'active' : '']"
                    @click="handleTogglePole(min.id, pole.id)"
                  >
                    <span class="truncate">{{ pole.nom }}</span>
                  </button>
                </div>
              </div>
            </Transition>
          </div>
        </div>
      </section>

      <section class="security-box">
        <div class="mb-4 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <ShieldCheck class="size-4 text-slate-500" />
            <h4 class="text-[10px] font-black tracking-widest text-slate-700 uppercase">
              Accès Applicatif
            </h4>
          </div>
          <button
            type="button"
            class="text-primary-600 text-[11px] font-bold"
            @click="showUserAccount = !showUserAccount"
          >
            {{ showUserAccount ? 'Révoquer' : 'Accorder' }}
          </button>
        </div>
        <Transition name="form-expand">
          <div
            v-if="showUserAccount"
            class="grid grid-cols-1 gap-4 border-t border-slate-200/60 pt-4 md:grid-cols-2"
          >
            <div class="form-group">
              <label>Utilisateur</label
              ><input
                v-if="form.utilisateur"
                v-model="form.utilisateur.username"
                type="text"
                class="input-field"
              />
            </div>
            <div class="form-group">
              <label>Password</label>
              <div class="input-wrapper">
                <Lock class="input-icon" /><input
                  v-if="form.utilisateur"
                  v-model="form.utilisateur.password"
                  type="password"
                  class="input-field with-icon"
                />
              </div>
            </div>
          </div>
        </Transition>
      </section>
    </form>

    <template #footer>
      <div class="flex w-full items-center gap-3">
        <button class="btn btn-secondary btn-lg flex-1" @click="emit('close')">Annuler</button>
        <button
          type="submit"
          form="profileForm"
          :disabled="isSubmitting"
          class="btn btn-primary btn-lg flex-1"
        >
          {{ isSubmitting ? 'Envoi...' : editingProfile ? 'Mettre à jour' : 'Créer le profil' }}
        </button>
      </div>
    </template>
  </AppDrawer>
</template>

<style scoped>
@reference "../../assets/css/main.css";

/* Headers */
.section-header {
  @apply flex items-center gap-2 border-b border-slate-100 pb-1.5 text-[10px] font-black tracking-widest text-slate-400 uppercase;
}
.form-group {
  @apply flex flex-col gap-1.5;
}
.form-group label {
  @apply ml-0.5 text-[10px] font-bold text-slate-500 uppercase;
}

/* Inputs */
.input-field {
  @apply w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 transition-all outline-none hover:border-slate-300;
}
.input-field:focus {
  border-color: var(--color-primary-600);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-primary-600) 15%, transparent);
}
.input-wrapper {
  @apply relative flex items-center;
}
.input-icon {
  @apply pointer-events-none absolute left-3 size-3.5 text-slate-400;
}
.input-field.with-icon {
  @apply pl-9;
}

/* Campus UI */
.campus-tag {
  @apply flex items-center gap-1.5 rounded-full px-3 py-1 text-[11px] font-bold;
  background-color: color-mix(in srgb, var(--color-primary-600) 10%, white);
  border: 1px solid color-mix(in srgb, var(--color-primary-600) 20%, white);
  color: var(--color-primary-700);
}
.campus-tag-more {
  @apply rounded-full bg-slate-100 px-3 py-1 text-[11px] font-bold text-slate-600;
}

/* Accordéon & Pôles */
.ministere-accordion {
  @apply overflow-hidden rounded-xl border border-slate-200 bg-white transition-all duration-200;
}
.ministere-accordion.is-active {
  border-color: color-mix(in srgb, var(--color-primary-600) 40%, white);
}
.pole-pill {
  @apply flex items-center justify-center rounded-lg border border-slate-200 bg-white px-3 py-2 text-[11px] font-bold text-slate-600 transition-all active:scale-95;
}
.pole-pill.active {
  border-color: color-mix(in srgb, var(--color-primary-600) 30%, transparent);
  background-color: color-mix(in srgb, var(--color-primary-600) 10%, white);
  color: var(--color-primary-700);
}

/* Toggle & Security */
.status-toggle-card {
  @apply flex items-center justify-between rounded-xl border border-slate-200 bg-white p-3.5;
}
.toggle-pill {
  @apply relative h-5 w-10 rounded-full bg-slate-200 transition-colors;
}
.toggle-pill.active {
  background-color: #10b981;
}
.toggle-circle {
  @apply absolute top-0.5 left-0.5 size-4 rounded-full bg-white shadow-md transition-transform duration-200;
}
.security-box {
  @apply rounded-xl border border-slate-200 bg-slate-50/50 p-4;
}

/* Animations */
.form-expand-enter-active,
.form-expand-leave-active {
  transition: all 0.3s ease-in-out;
  max-height: 500px;
}
.form-expand-enter-from,
.form-expand-leave-to {
  opacity: 0;
  max-height: 0;
  overflow: hidden;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #e2e8f0;
  border-radius: 10px;
}
</style>

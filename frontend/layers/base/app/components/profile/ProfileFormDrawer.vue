<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { User, MapPin, Building2, ShieldCheck, Info } from 'lucide-vue-next'
import { useProfileFormLogic } from '../../composables/useProfileFormLogic'
import { useDraftProfile } from '../../composables/useDraftProfile'
import FormSection from '../FormSection.vue'

// Import des sous-composants atomiques
import ProfileBasicInfo from './ProfileBasicInfo.vue'
import ProfileCampusSelector from './ProfileCampusSelector.vue'
import ProfileMinistereManager from './ProfileMinistereManager.vue'
import ProfileSecurityAccess from './ProfileSecurityAccess.vue'

import type { ProfilCreateFull, ProfilReadFull } from '~~/layers/base/types/profiles'
import type { CampusRead } from '~~/layers/base/types/campus'
import type { MinistereReadWithRelations } from '~~/layers/base/types/ministere'

interface Props {
  isOpen: boolean
  editingProfile: ProfilReadFull | null
  campuses: CampusRead[]
  ministeresDetailed: MinistereReadWithRelations[]
  isSubmitting: boolean
  isLoadingReferences?: boolean
  prefillCampusId?: string | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
  submit: [payload: ProfilCreateFull]
  'campus-changed': [campusId: string]
}>()

const { mapProfileToForm, toggleMinistere, togglePole } = useProfileFormLogic()
const { saveDraft, restoreDraft, clearDraft, hasDraft } = useDraftProfile()

const showDraftBanner = ref(false)

// --- ÉTAT DU FORMULAIRE ---
const EMPTY_UTILISATEUR = { username: '', password: '', actif: true, roles_ids: [] }

const form = ref<ProfilCreateFull>({
  nom: '',
  prenom: '',
  email: '',
  telephone: '',
  actif: true,
  campus_ids: [],
  campus_principal_id: null,
  ministere_ids: [],
  pole_ids: [],
  role_codes: [],
  utilisateur: { ...EMPTY_UTILISATEUR },
})

// --- GESTION DES SECTIONS PLIABLES ---
// On utilise un Set pour permettre l'ouverture de plusieurs sections simultanément
const activeSections = ref(new Set(['basic']))

const toggleSection = (id: string) => {
  if (activeSections.value.has(id)) {
    activeSections.value.delete(id)
  } else {
    activeSections.value.add(id)
  }
}

// --- LOGIQUE DE PRÉ-REMPLISSAGE ---
watch(
  () => props.isOpen,
  (open) => {
    if (!open) return
    if (props.editingProfile) {
      form.value = mapProfileToForm(props.editingProfile)
      // En édition, on ouvre souvent les sections avec du contenu
      if (form.value.campus_ids.length > 0) activeSections.value.add('campus')
      if (form.value.ministere_ids.length > 0) activeSections.value.add('ministeres')
      showDraftBanner.value = false
    } else {
      resetForm()
      showDraftBanner.value = hasDraft.value
    }
  },
  { immediate: true },
)

const resetForm = () => {
  const prefill = props.prefillCampusId ?? null
  form.value = {
    nom: '',
    prenom: '',
    email: '',
    telephone: '',
    actif: true,
    campus_ids: prefill ? [prefill] : [],
    campus_principal_id: prefill,
    ministere_ids: [],
    pole_ids: [],
    role_codes: [],
    utilisateur: { ...EMPTY_UTILISATEUR },
  }
  if (prefill) activeSections.value = new Set(['basic', 'campus'])
  else activeSections.value = new Set(['basic'])
}

const restoreFromDraft = () => {
  const saved = restoreDraft()
  if (saved) {
    form.value = saved
    if (saved.campus_ids.length > 0) activeSections.value.add('campus')
    if (saved.ministere_ids.length > 0) activeSections.value.add('ministeres')
    if ((saved.role_codes?.length ?? 0) > 0) activeSections.value.add('roles')
  }
  showDraftBanner.value = false
}

const ignoreDraft = () => {
  clearDraft()
  showDraftBanner.value = false
}

const deleteDraft = () => {
  clearDraft()
  resetForm()
  showDraftBanner.value = false
}

const handleCancel = () => {
  if (!props.editingProfile) clearDraft()
  emit('close')
}

// Auto-save brouillon à chaque modification (création uniquement)
watch(
  form,
  (newForm) => {
    if (!props.editingProfile) saveDraft(newForm)
  },
  { deep: true },
)

// Auto-sélection du campus principal
watch(
  () => form.value.campus_ids,
  (ids) => {
    if (ids.length === 1) {
      form.value.campus_principal_id = ids[0]
    } else if (form.value.campus_principal_id && !ids.includes(form.value.campus_principal_id)) {
      form.value.campus_principal_id = ids.length === 1 ? ids[0] : null
    }
  },
)

const onSetPrincipal = (id: string) => {
  form.value.campus_principal_id = id
}

watch(
  () => form.value.campus_principal_id,
  (campusId) => {
    if (campusId) emit('campus-changed', campusId)
  },
)

const campusBadge = computed<string | number | undefined>(() => {
  if (form.value.campus_ids.length === 0) return undefined
  if (form.value.campus_principal_id) {
    const principal = props.campuses.find((c) => c.id === form.value.campus_principal_id)
    return principal?.nom ?? form.value.campus_ids.length
  }
  return form.value.campus_ids.length
})

// --- HANDLERS ÉVÉNEMENTS ---
const onToggleMin = (min: MinistereReadWithRelations) => {
  const res = toggleMinistere(min, form.value.ministere_ids, form.value.pole_ids)
  form.value.ministere_ids = res.ministere_ids
  form.value.pole_ids = res.pole_ids
}

const onTogglePole = (mId: string, pId: string) => {
  const res = togglePole(
    mId,
    pId,
    props.ministeresDetailed,
    form.value.ministere_ids,
    form.value.pole_ids,
  )
  form.value.ministere_ids = res.ministere_ids
  form.value.pole_ids = res.pole_ids
}

const handleSubmit = () => {
  const payload = JSON.parse(JSON.stringify(form.value))
  clearDraft()
  emit('submit', payload)
}
</script>

<template>
  <AppDrawer
    :isOpen="isOpen"
    :title="
      editingProfile
        ? `Édition : ${editingProfile.prenom} ${editingProfile.nom}`
        : 'Nouveau Collaborateur'
    "
    initialSize="half"
    @close="emit('close')"
  >
    <form id="profileForm" class="flex flex-col gap-2 pb-10" @submit.prevent="handleSubmit">
      <!-- Bannière de restauration de brouillon (création uniquement) -->
      <div
        v-if="showDraftBanner"
        class="flex items-center justify-between gap-3 rounded-xl border border-amber-100 bg-amber-50 px-4 py-3 text-xs text-amber-800"
      >
        <span>Un brouillon non terminé a été trouvé.</span>
        <div class="flex shrink-0 items-center gap-3">
          <button
            type="button"
            class="font-semibold underline underline-offset-2 hover:text-amber-900"
            @click="restoreFromDraft"
          >
            Reprendre
          </button>
          <span class="text-amber-300">|</span>
          <button type="button" class="text-amber-600 hover:text-amber-800" @click="ignoreDraft">
            Ignorer
          </button>
          <span class="text-amber-300">|</span>
          <button type="button" class="text-rose-400 hover:text-rose-600" @click="deleteDraft">
            Supprimer
          </button>
        </div>
      </div>

      <FormSection
        title="Informations Personnelles"
        :icon="User"
        :isOpen="activeSections.has('basic')"
        @toggle="toggleSection('basic')"
      >
        <ProfileBasicInfo v-model="form" />
      </FormSection>

      <FormSection
        title="Affectation Campus"
        :icon="MapPin"
        :isOpen="activeSections.has('campus')"
        :badge="campusBadge"
        @toggle="toggleSection('campus')"
      >
        <ProfileCampusSelector
          v-model="form.campus_ids"
          :campuses="campuses"
          :principalId="form.campus_principal_id"
          @set-principal="onSetPrincipal"
        />
        <div
          v-if="form.campus_ids.length > 1 && !form.campus_principal_id"
          class="mt-2 flex items-center gap-1 text-[11px] text-amber-600"
        >
          <Info class="size-3 shrink-0" />
          <span>Cliquez sur la couronne d'un campus pour le définir comme principal.</span>
        </div>
      </FormSection>

      <FormSection
        title="Ministères, Pôles & Rôles"
        :icon="Building2"
        :isOpen="activeSections.has('ministeres')"
        :badge="form.pole_ids.length > 0 ? form.pole_ids.length : undefined"
        @toggle="toggleSection('ministeres')"
      >
        <ProfileMinistereManager
          :ministeres="ministeresDetailed"
          :ministereIds="form.ministere_ids"
          :poleIds="form.pole_ids"
          :roleCodes="form.role_codes ?? []"
          @toggle-ministere="onToggleMin"
          @toggle-pole="onTogglePole"
          @update:role-codes="(v) => (form.role_codes = v)"
        />
      </FormSection>

      <FormSection
        title="Accès Applicatif"
        :icon="ShieldCheck"
        :isOpen="activeSections.has('security')"
        :badge="form.utilisateur ? 'Actif' : undefined"
        @toggle="toggleSection('security')"
      >
        <ProfileSecurityAccess
          v-model="form.utilisateur"
          :existingRoles="editingProfile?.utilisateur?.roles?.map((r) => r.libelle) ?? []"
        />
      </FormSection>

      <div class="mt-4 flex items-start gap-3 rounded-xl border border-blue-100 bg-blue-50/50 p-4">
        <Info class="mt-0.5 size-4 text-blue-500" />
        <p class="text-[11px] leading-relaxed text-blue-700">
          Les modifications sur les accès applicatifs prendront effet lors de la prochaine
          reconnexion de l'utilisateur.
        </p>
      </div>
    </form>

    <template #footer>
      <div class="flex w-full items-center gap-3">
        <button type="button" class="btn btn-secondary btn-lg flex-1" @click="handleCancel">
          Annuler
        </button>
        <button
          type="submit"
          form="profileForm"
          :disabled="isSubmitting"
          class="btn btn-primary btn-lg flex-1"
        >
          <span v-if="isSubmitting">Traitement...</span>
          <span v-else>{{
            editingProfile ? 'Enregistrer les modifications' : 'Créer le profil'
          }}</span>
        </button>
      </div>
    </template>
  </AppDrawer>
</template>

<style scoped>
@reference "../../assets/css/main.css";

/* Conteneur principal du formulaire avec padding horizontal */
#profileForm {
  @apply px-2;
}

/* On garde les utilitaires de scroll au cas où le contenu déborde */
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #e2e8f0;
  border-radius: 10px;
}
</style>

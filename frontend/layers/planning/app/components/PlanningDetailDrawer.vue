<template>
  <AppDrawer
    :isOpen="isOpen"
    :title="drawerTitle"
    :initialSize="internalMode !== 'detail' ? 'half' : undefined"
    @close="handleClose"
  >
    <PlanningDetailView
      v-if="internalMode === 'detail' && event"
      :event="event"
      :planning="planning"
    />
    <PlanningFormView v-else-if="internalMode !== 'detail'" />

    <!-- ================================================================
         FOOTER DÉTAIL
         ================================================================ -->
    <template v-if="internalMode === 'detail'" #footer>
      <div class="space-y-2">
        <div
          v-if="canChangeStatus && allowedTransitions.length > 0 && !confirmingCancel"
          ref="statusDropdownRef"
          class="relative"
        >
          <button
            type="button"
            :disabled="isUpdating"
            class="flex w-full items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm transition-colors hover:border-slate-300 hover:bg-slate-50 disabled:opacity-50"
            @click="statusDropdownOpen = !statusDropdownOpen"
          >
            <div class="flex items-center gap-2">
              <span class="text-xs text-slate-400">Statut actuel</span>
              <span :class="currentStatusBadgeClass">{{ currentStatusLabel }}</span>
            </div>
            <div class="flex items-center gap-1.5">
              <Loader2 v-if="isUpdating" class="size-4 animate-spin text-slate-400" />
              <template v-else>
                <span class="text-xs font-medium text-slate-500">Changer</span>
                <ChevronDown
                  class="size-4 text-slate-400 transition-transform duration-150"
                  :class="statusDropdownOpen ? 'rotate-180' : ''"
                />
              </template>
            </div>
          </button>

          <Transition
            enterActiveClass="transition-opacity duration-150"
            enterFromClass="opacity-0"
            enterToClass="opacity-100"
            leaveActiveClass="transition-opacity duration-100"
            leaveFromClass="opacity-100"
            leaveToClass="opacity-0"
          >
            <div
              v-if="statusDropdownOpen"
              class="absolute right-0 bottom-full left-0 z-50 mb-2 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xl"
            >
              <button
                v-for="opt in transitionOptions"
                :key="opt.code"
                type="button"
                class="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors"
                :class="opt.code === 'ANNULE' ? 'hover:bg-red-50' : 'hover:bg-slate-50'"
                @click="handleTransitionSelect(opt.code)"
              >
                <div
                  class="flex size-8 shrink-0 items-center justify-center rounded-full"
                  :class="opt.iconBg"
                >
                  <component :is="opt.icon" class="size-4" :class="opt.iconClass" />
                </div>
                <div class="min-w-0 flex-1">
                  <div class="text-sm font-semibold" :class="opt.labelClass">{{ opt.label }}</div>
                  <div class="text-xs text-slate-400">{{ opt.description }}</div>
                </div>
              </button>
            </div>
          </Transition>
        </div>

        <div class="flex gap-3">
          <button
            v-if="canEdit"
            class="flex-1 rounded-lg px-4 py-2 text-sm font-bold text-white transition-colors"
            style="background-color: var(--color-primary-600)"
            @click="switchToEdit"
          >
            Modifier
          </button>
          <button
            v-if="canWrite"
            type="button"
            class="rounded-lg border border-red-100 px-4 py-2 text-sm font-medium text-red-500 transition-colors hover:bg-red-50"
            @click="confirmingDelete = true"
          >
            Supprimer
          </button>
          <button
            class="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-800"
            @click="handleClose"
          >
            Fermer
          </button>
        </div>

        <!-- Bouton Save as Template (write uniquement) -->
        <button
          v-if="canWrite && planning?.id"
          type="button"
          class="flex w-full items-center justify-center gap-2 rounded-xl border border-indigo-100 px-4 py-2 text-xs font-semibold text-indigo-600 transition-colors hover:bg-indigo-50"
          @click="showTemplateModal = true"
        >
          <BookmarkPlus class="size-4" />
          Sauvegarder comme template
        </button>
      </div>
    </template>

    <!-- ================================================================
         FOOTER FORMULAIRE
         ================================================================ -->
    <template v-else #footer>
      <p v-if="apiError" class="mb-2 text-xs text-red-500">{{ apiError }}</p>
      <div class="flex w-full items-center gap-3">
        <button type="button" class="footer-btn-secondary" @click="handleClose">Annuler</button>
        <div class="flex-1"></div>

        <!-- Dropdown statut cible -->
        <div ref="formStatusDropdownRef" class="relative">
          <button
            type="button"
            class="footer-btn-outline gap-1"
            :disabled="formStatusOptions.length <= 1"
            @click="formStatusDropdownOpen = !formStatusDropdownOpen"
          >
            <span>{{ formStatusLabel }}</span>
            <ChevronDown
              v-if="formStatusOptions.length > 1"
              class="size-3.5 transition-transform"
              :class="{ 'rotate-180': formStatusDropdownOpen }"
            />
          </button>
          <Transition
            enterActiveClass="transition duration-100 ease-out"
            enterFromClass="opacity-0 scale-95"
            enterToClass="opacity-100 scale-100"
            leaveActiveClass="transition duration-75 ease-in"
            leaveFromClass="opacity-100 scale-100"
            leaveToClass="opacity-0 scale-95"
          >
            <div
              v-if="formStatusDropdownOpen"
              class="absolute right-0 bottom-full mb-1 w-36 origin-bottom-right rounded-xl border border-slate-200 bg-white py-1 shadow-lg"
            >
              <button
                v-for="opt in formStatusOptions"
                :key="opt.code"
                type="button"
                class="flex w-full items-center px-3 py-2 text-left text-xs font-medium transition-colors hover:bg-slate-50"
                :class="
                  opt.code === formTargetStatus ? 'font-semibold text-blue-600' : 'text-slate-700'
                "
                @click="((formTargetStatus = opt.code), (formStatusDropdownOpen = false))"
              >
                {{ opt.label }}
              </button>
            </div>
          </Transition>
        </div>

        <!-- Bouton Enregistrer -->
        <button
          type="button"
          class="footer-btn-primary"
          :disabled="!canSave || isSaving"
          @click="save()"
        >
          <Loader2 v-if="isSaving" class="size-4 animate-spin" />
          <Save v-else class="size-4" />
          Enregistrer
        </button>
      </div>
    </template>
  </AppDrawer>

  <!-- Modal Save as Template (en dehors du drawer pour éviter les conflits de slot) -->
  <SaveAsTemplateModal
    v-if="planning?.id"
    :isOpen="showTemplateModal"
    :planningId="planning.id"
    @close="showTemplateModal = false"
    @saved="showTemplateModal = false"
  />
</template>

<script setup lang="ts">
import { ref, computed, watch, provide } from 'vue'
import { BookmarkPlus, ChevronDown, Loader2, Save } from 'lucide-vue-next'
import AppDrawer from '~~/layers/base/app/components/AppDrawer.vue'
import { usePlanning } from '../composables/usePlanning'
import { usePlanningPermissions } from '../composables/usePlanningPermissions'
import { usePlanningWorkflow, planningWorkflowKey } from '../composables/usePlanningWorkflow'
import {
  usePlanningDetailHelpers,
  planningDetailHelpersKey,
} from '../composables/usePlanningDetailHelpers'
import { usePlanningForm, planningFormKey } from '../composables/usePlanningForm'
import PlanningDetailView from './PlanningDetailView.vue'
import PlanningFormView from './PlanningFormView.vue'
import SaveAsTemplateModal from './SaveAsTemplateModal.vue'
import type { PlanningEvent, PlanningFullRead } from '../types/planning.types'
import { useUIStore } from '~~/layers/base/app/stores/useUiStore'

// -----------------------------------------------------------------------
// Props & Emits
// -----------------------------------------------------------------------
const props = defineProps<{
  mode: 'detail' | 'create' | 'edit' | null
  event?: PlanningEvent | null
  planning?: PlanningFullRead | null
  prefillDate?: string | null
}>()

const emit = defineEmits<{
  close: []
  saved: [planning: PlanningFullRead, isNew: boolean]
  statusChanged: [updated: PlanningFullRead]
  deleted: [id: string]
}>()

// -----------------------------------------------------------------------
// Services & stores
// -----------------------------------------------------------------------
const { ministereColorMap } = usePlanning()
const uiStore = useUIStore()
const { canWrite, canChangeStatus } = usePlanningPermissions()

const userCampuses = computed(() => uiStore.myCampuses)
const userCampusPrincipalId = computed<string | null>(() => uiStore.currentCampus?.id ?? null)

// -----------------------------------------------------------------------
// État interne du mode
// -----------------------------------------------------------------------
const internalMode = ref<'detail' | 'create' | 'edit'>(props.mode ?? 'detail')
const isOpen = computed(() => props.mode !== null)

const drawerTitle = computed(() => {
  if (internalMode.value === 'create') return 'Nouveau planning'
  if (internalMode.value === 'edit') return 'Modifier le planning'
  return props.event?.title ?? ''
})

// Refs réactifs vers les props pour les passer aux composables
const planningRef = computed(() => props.planning ?? null)
const eventRef = computed(() => props.event ?? null)
const prefillDateRef = computed(() => props.prefillDate ?? null)

// -----------------------------------------------------------------------
// Composables
// -----------------------------------------------------------------------
const form = usePlanningForm(
  planningRef,
  prefillDateRef,
  internalMode,
  userCampuses,
  userCampusPrincipalId,
  ministereColorMap,
  canWrite,
  {
    onSaved: (p, isNew) => emit('saved', p, isNew),
    onClose: () => emit('close'),
  },
)

const workflow = usePlanningWorkflow(planningRef, eventRef, canWrite, {
  onStatusChanged: (updated) => emit('statusChanged', updated),
  onDeleted: (id) => emit('deleted', id),
  onClose: () => emit('close'),
})

const helpers = usePlanningDetailHelpers(
  planningRef,
  eventRef,
  form.campusTeam,
  form.roles,
  form.campusMinistereColorMap,
  ministereColorMap,
  uiStore,
)

// -----------------------------------------------------------------------
// Provide — sous-composants lisent via inject
// -----------------------------------------------------------------------
provide(planningWorkflowKey, workflow)
provide(planningDetailHelpersKey, helpers)
provide(planningFormKey, form)
provide('userCampuses', userCampuses)

// -----------------------------------------------------------------------
// Destructuration pour le template du shell (footer + header)
// -----------------------------------------------------------------------
const {
  // workflow — footer détail
  canEdit,
  confirmingCancel,
  confirmingDelete,
  isUpdating,
  statusDropdownRef, // lié au DOM via ref="statusDropdownRef" dans le template
  statusDropdownOpen,
  transitionOptions,
  allowedTransitions,
  currentStatusBadgeClass,
  currentStatusLabel,
  handleTransitionSelect,
  loadFullPlanning,
  resetState,
} = workflow

const {
  // form — footer formulaire
  apiError,
  formStatusDropdownRef, // lié au DOM via ref="formStatusDropdownRef" dans le template
  formStatusDropdownOpen,
  formStatusOptions,
  formStatusLabel,
  formTargetStatus,
  canSave,
  isSaving,
  save,
  initForm,
  loadRoles,
  loadMinistreresForCampus,
} = form

// -----------------------------------------------------------------------
// Watch — transitions de mode
// -----------------------------------------------------------------------
watch(
  () => props.mode,
  async (newMode) => {
    if (newMode === null) return
    internalMode.value = newMode

    if (newMode === 'create' || newMode === 'edit') {
      await initForm()
      await loadRoles()
    }

    if (newMode === 'detail') {
      const campusId = props.planning?.activite?.campus_id
      if (campusId && !form.campusTeam.value) {
        await loadMinistreresForCampus(campusId)
      }
      if (!form.roles.value.length) {
        await loadRoles()
      }
      if (props.planning?.id) {
        loadFullPlanning(props.planning.id)
      }
    } else {
      resetState()
    }
  },
)

// -----------------------------------------------------------------------
// Template modal
// -----------------------------------------------------------------------
const showTemplateModal = ref(false)

// -----------------------------------------------------------------------
// Actions du shell
// -----------------------------------------------------------------------
async function switchToEdit(): Promise<void> {
  internalMode.value = 'edit'
  await initForm()
  await loadRoles()
}

function handleClose(): void {
  if (isSaving.value || isUpdating.value) return
  emit('close')
}
</script>

<style scoped>
@reference "~~/layers/base/app/assets/css/main.css";

.footer-btn-primary {
  @apply flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-bold text-white transition-all active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50;
  background-color: var(--color-primary-600);
}
.footer-btn-primary:hover:not(:disabled) {
  background-color: var(--color-primary-700);
}

.footer-btn-outline {
  @apply flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2.5 text-xs font-semibold text-slate-600 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50;
}

.footer-btn-secondary {
  @apply rounded-xl border border-slate-200 px-4 py-2.5 text-xs font-bold text-slate-500 transition-colors hover:bg-slate-50 hover:text-slate-700;
}
</style>

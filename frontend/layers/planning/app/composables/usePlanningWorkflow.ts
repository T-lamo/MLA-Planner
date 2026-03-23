import {
  ref,
  computed,
  onMounted,
  onUnmounted,
  type Component,
  type InjectionKey,
  type Ref,
} from 'vue'
import { CheckCircle2, CheckCheck, XCircle, FilePen } from 'lucide-vue-next'
import { PlanningRepository } from '../repositories/PlanningRepository'
import type { PlanningEvent, PlanningFullRead } from '../types/planning.types'

export interface TransitionOption {
  code: string
  label: string
  description: string
  icon: Component
  iconClass: string
  iconBg: string
  labelClass: string
}

export const TRANSITION_META: Record<string, Omit<TransitionOption, 'code'>> = {
  PUBLIE: {
    label: 'Publier',
    description: 'Rendre ce planning visible aux membres',
    icon: CheckCircle2,
    iconClass: 'text-emerald-600',
    iconBg: 'bg-emerald-50',
    labelClass: 'text-emerald-700',
  },
  TERMINE: {
    label: 'Marquer comme terminé',
    description: 'Clore définitivement ce planning',
    icon: CheckCheck,
    iconClass: 'text-slate-600',
    iconBg: 'bg-slate-100',
    labelClass: 'text-slate-700',
  },
  ANNULE: {
    label: 'Annuler le planning',
    description: 'Action irréversible',
    icon: XCircle,
    iconClass: 'text-red-500',
    iconBg: 'bg-red-50',
    labelClass: 'text-red-700',
  },
  BROUILLON: {
    label: 'Repasser en brouillon',
    description: 'Retirer de la publication temporairement',
    icon: FilePen,
    iconClass: 'text-amber-600',
    iconBg: 'bg-amber-50',
    labelClass: 'text-amber-700',
  },
}

export type PlanningWorkflow = ReturnType<typeof usePlanningWorkflow>
export const planningWorkflowKey: InjectionKey<PlanningWorkflow> = Symbol('planningWorkflow')

export function usePlanningWorkflow(
  planning: Ref<PlanningFullRead | null | undefined>,
  planningEvent: Ref<PlanningEvent | null | undefined>,
  canWrite: Ref<boolean>,
  callbacks: {
    onStatusChanged: (updated: PlanningFullRead) => void
    onDeleted: (id: string) => void
    onClose: () => void
  },
) {
  const repo = new PlanningRepository()
  const notify = useMLANotify()
  const { handleError } = useFormError()

  // -----------------------------------------------------------------------
  // State
  // -----------------------------------------------------------------------
  const detailPlanningFull = ref<PlanningFullRead | null>(null)
  const isUpdating = ref(false)
  const pendingStatus = ref<string | null>(null)
  const confirmingCancel = ref(false)
  const confirmingDelete = ref(false)
  const isDeleting = ref(false)
  const workflowError = ref<string | null>(null)
  const statusDropdownOpen = ref(false)
  const statusDropdownRef = ref<HTMLElement | null>(null)

  // -----------------------------------------------------------------------
  // Computed
  // -----------------------------------------------------------------------
  const allowedTransitions = computed<string[]>(
    () =>
      detailPlanningFull.value?.view_context?.allowed_transitions ??
      planning.value?.view_context?.allowed_transitions ??
      [],
  )

  const transitionOptions = computed<TransitionOption[]>(() =>
    allowedTransitions.value
      .filter((code) => code in TRANSITION_META)
      .map((code) => ({ code, ...TRANSITION_META[code] }) as TransitionOption),
  )

  const currentStatusLabel = computed<string>(() => {
    const labels: Record<string, string> = {
      BROUILLON: 'Brouillon',
      PUBLIE: 'Publié',
      ANNULE: 'Annulé',
      TERMINE: 'Terminé',
    }
    return labels[planning.value?.statut_code ?? ''] ?? planning.value?.statut_code ?? ''
  })

  const currentStatusBadgeClass = computed<string>(() => {
    const s = planning.value?.statut_code ?? ''
    if (s === 'PUBLIE')
      return 'rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-700'
    if (s === 'ANNULE' || s === 'TERMINE')
      return 'rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-600'
    return 'rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-bold text-amber-700'
  })

  const canEdit = computed<boolean>(() => {
    if (!canWrite.value) return false
    const s = planningEvent.value?.extendedProps.statut
    return s !== 'ANNULE' && s !== 'TERMINE'
  })

  // -----------------------------------------------------------------------
  // Actions
  // -----------------------------------------------------------------------
  function loadFullPlanning(id: string): void {
    detailPlanningFull.value = null
    repo
      .getFullPlanning(id)
      .then((full) => {
        detailPlanningFull.value = full
      })
      .catch(() => {})
  }

  function resetState(): void {
    confirmingCancel.value = false
    confirmingDelete.value = false
    statusDropdownOpen.value = false
    workflowError.value = null
    detailPlanningFull.value = null
  }

  function handleTransitionSelect(code: string): void {
    statusDropdownOpen.value = false
    if (code === 'ANNULE') {
      confirmingCancel.value = true
    } else {
      onStatusChange(code)
    }
  }

  function onStatusChange(status: string): void {
    workflowError.value = null
    confirmingCancel.value = false
    executeStatusChange(status)
  }

  async function executeStatusChange(status: string): Promise<void> {
    if (!planning.value) return
    isUpdating.value = true
    pendingStatus.value = status
    workflowError.value = null
    try {
      const updated = await repo.updateStatus(planning.value.id, status)
      notify.success('Statut mis à jour', status)
      callbacks.onStatusChanged(updated)
      callbacks.onClose()
    } catch (e) {
      workflowError.value = handleError(e, 'Erreur lors de la mise à jour du statut')
      confirmingCancel.value = false
    } finally {
      isUpdating.value = false
      pendingStatus.value = null
    }
  }

  async function executeDelete(): Promise<void> {
    if (!planning.value) return
    isDeleting.value = true
    workflowError.value = null
    try {
      await repo.deleteFull(planning.value.id)
      notify.success('Planning supprimé')
      callbacks.onDeleted(planning.value.id)
      callbacks.onClose()
    } catch (e) {
      workflowError.value = handleError(e, 'Erreur lors de la suppression')
      confirmingDelete.value = false
    } finally {
      isDeleting.value = false
    }
  }

  // -----------------------------------------------------------------------
  // Click-outside — ferme le dropdown statut en mode détail
  // -----------------------------------------------------------------------
  const _onClickOutside = (e: MouseEvent) => {
    if (statusDropdownRef.value && !statusDropdownRef.value.contains(e.target as Node)) {
      statusDropdownOpen.value = false
    }
  }
  onMounted(() => document.addEventListener('mousedown', _onClickOutside))
  onUnmounted(() => document.removeEventListener('mousedown', _onClickOutside))

  return {
    detailPlanningFull,
    isUpdating,
    pendingStatus,
    confirmingCancel,
    confirmingDelete,
    isDeleting,
    workflowError,
    statusDropdownOpen,
    statusDropdownRef,
    allowedTransitions,
    transitionOptions,
    currentStatusLabel,
    currentStatusBadgeClass,
    canEdit,
    loadFullPlanning,
    resetState,
    handleTransitionSelect,
    executeStatusChange,
    executeDelete,
  }
}

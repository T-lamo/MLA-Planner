import {
  ref,
  reactive,
  computed,
  watch,
  onMounted,
  onUnmounted,
  type ComputedRef,
  type InjectionKey,
  type Ref,
} from 'vue'
import { PlanningRepository } from '../repositories/PlanningRepository'
import type {
  AffectationFormItem,
  AffectationStatus,
  ActiviteFormState,
  ApplyTemplateResult,
  CampusTeamRead,
  MinistereColor,
  PlanningFullRead,
  PlanningTemplateRead,
  RoleCompetenceRead,
  SlotFormItem,
  TeamMemberRead,
  WarningIndispo,
  WarningMembreIgnore,
} from '../types/planning.types'
import { getMinistereColor } from '../types/planning.types'
import { TRANSITION_META } from './usePlanningWorkflow'
import { findMinistreForMembreInTeam } from './usePlanningDetailHelpers'

export interface SlotPickerState {
  open: boolean
  ministereId: string
  memberQuery: string
  memberId: string
  memberPrenom: string
  memberNom: string
  memberRoles: string[]
  roleCode: string
  showMemberList: boolean
}

function defaultPicker(): SlotPickerState {
  return {
    open: false,
    ministereId: '',
    memberQuery: '',
    memberId: '',
    memberPrenom: '',
    memberNom: '',
    memberRoles: [],
    roleCode: '',
    showMemberList: false,
  }
}

/** Calcule HH:MM à partir d'une date ISO et d'un offset en minutes. */
function offsetToHHMM(baseDateStr: string, offsetMinutes: number): string {
  if (!baseDateStr) return ''
  const base = new Date(baseDateStr)
  if (isNaN(base.getTime())) return ''
  const total = new Date(base.getTime() + offsetMinutes * 60_000)
  return `${String(total.getHours()).padStart(2, '0')}:${String(total.getMinutes()).padStart(
    2,
    '0',
  )}`
}

export type PlanningForm = ReturnType<typeof usePlanningForm>
export const planningFormKey: InjectionKey<PlanningForm> = Symbol('planningForm')

export function usePlanningForm(
  planning: Ref<PlanningFullRead | null | undefined>,
  prefillDate: Ref<string | null | undefined>,
  internalMode: Ref<'detail' | 'create' | 'edit'>,
  userCampuses: ComputedRef<Array<{ id: string; nom: string }>>,
  userCampusPrincipalId: ComputedRef<string | null>,
  ministereColorMap: ComputedRef<Map<string, MinistereColor>>,
  canWrite: Ref<boolean>,
  callbacks: {
    onSaved: (planning: PlanningFullRead, isNew: boolean) => void
    onClose: () => void
  },
) {
  const repo = new PlanningRepository()
  const notify = useMLANotify()
  const { handleError } = useFormError()

  let tempIdCounter = 0
  const newTempId = () => `tmp-${++tempIdCounter}`

  // -----------------------------------------------------------------------
  // Campus team & rôles (partagés avec le mode détail via le shell)
  // -----------------------------------------------------------------------
  const campusTeam = ref<CampusTeamRead | null>(null)
  const isLoadingMinisteres = ref(false)
  const roles = ref<RoleCompetenceRead[]>([])

  const campusMinisteres = computed(() => campusTeam.value?.ministeres ?? [])

  const campusMinistereColorMap = computed<Map<string, MinistereColor>>(() => {
    const ids = campusMinisteres.value.map((m) => m.id)
    const map = new Map<string, MinistereColor>()
    ids.forEach((id) => map.set(id, getMinistereColor(id, ids)))
    return map
  })

  /**
   * Charge l'équipe du campus (ministères + membres).
   * @param preserveMinistere - `true` lors de l'init du formulaire en mode edit :
   *   ne pas effacer la sélection du ministère même s'il n'est pas dans la liste
   *   retournée par l'API (ex : admin qui édite un planning d'un ministère auquel
   *   il n'appartient pas personnellement).
   */
  async function loadMinistreresForCampus(
    campusId: string,
    preserveMinistere = false,
  ): Promise<void> {
    if (!campusId) {
      campusTeam.value = null
      return
    }
    isLoadingMinisteres.value = true
    try {
      campusTeam.value = await repo.getCampusTeam(campusId)
      if (
        !preserveMinistere &&
        activiteForm.ministere_organisateur_id &&
        !campusMinisteres.value.some((m) => m.id === activiteForm.ministere_organisateur_id)
      ) {
        activiteForm.ministere_organisateur_id = ''
      }
    } catch {
      campusTeam.value = null
    } finally {
      isLoadingMinisteres.value = false
    }
  }

  async function loadRoles(): Promise<void> {
    try {
      roles.value = await repo.getRoleCompetences()
    } catch {
      // Rôles optionnels — pas de plantage si l'API échoue
    }
  }

  // -----------------------------------------------------------------------
  // Form state
  // -----------------------------------------------------------------------
  const activeSections = ref(new Set(['activite']))

  const activiteForm = reactive<ActiviteFormState>({
    type: '',
    date_debut: '',
    date_fin: '',
    lieu: '',
    description: '',
    campus_id: '',
    ministere_organisateur_id: '',
  })

  const slotsForm = ref<SlotFormItem[]>([])
  const slotPickers = ref<SlotPickerState[]>([])
  const selectedTemplateId = ref<string | null>(null)
  const templateApplied = ref(false)
  const applyWarningsIndispo = ref<WarningIndispo[]>([])
  const applyIgnoredMembres = ref<WarningMembreIgnore[]>([])
  const isSaving = ref(false)
  const apiError = ref<string | null>(null)
  const formTargetStatus = ref<string>('BROUILLON')
  const formStatusDropdownOpen = ref(false)
  const formStatusDropdownRef = ref<HTMLElement | null>(null)

  // -----------------------------------------------------------------------
  // Computed — validation & affichage
  // -----------------------------------------------------------------------
  const selectedMinistereColor = computed(() => {
    if (!activiteForm.ministere_organisateur_id) return null
    return (
      campusMinistereColorMap.value.get(activiteForm.ministere_organisateur_id) ??
      ministereColorMap.value.get(activiteForm.ministere_organisateur_id) ??
      null
    )
  })

  const dateError = computed(() => {
    if (!activiteForm.date_debut || !activiteForm.date_fin) return ''
    if (new Date(activiteForm.date_fin) <= new Date(activiteForm.date_debut)) {
      return 'La date de fin doit être après le début'
    }
    return ''
  })

  const isSection1Complete = computed(
    () =>
      !!activiteForm.type &&
      !!activiteForm.date_debut &&
      !!activiteForm.date_fin &&
      !dateError.value &&
      !!activiteForm.campus_id &&
      !!activiteForm.ministere_organisateur_id,
  )

  const totalAffectations = computed(() =>
    slotsForm.value.reduce((sum, s) => sum + s.affectations.length, 0),
  )

  const canSave = computed(() => isSection1Complete.value)

  const formStatusOptions = computed<Array<{ code: string; label: string }>>(() => {
    if (internalMode.value === 'create') {
      const opts: Array<{ code: string; label: string }> = [
        { code: 'BROUILLON', label: 'Brouillon' },
      ]
      if (canWrite.value) opts.push({ code: 'PUBLIE', label: 'Publier' })
      return opts
    }
    const currentCode = planning.value?.statut_code ?? 'BROUILLON'
    const statusLabels: Record<string, string> = {
      BROUILLON: 'Brouillon',
      PUBLIE: 'Publié',
      ANNULE: 'Annulé',
      TERMINE: 'Terminé',
    }
    const transitions = planning.value?.view_context?.allowed_transitions ?? []
    const opts: Array<{ code: string; label: string }> = [
      { code: currentCode, label: statusLabels[currentCode] ?? currentCode },
    ]
    transitions
      .filter((t) => t in TRANSITION_META)
      .forEach((t) => opts.push({ code: t, label: TRANSITION_META[t]?.label ?? t }))
    return opts
  })

  const formStatusLabel = computed<string>(() => {
    const labels: Record<string, string> = {
      BROUILLON: 'Brouillon',
      PUBLIE: 'Publier',
      ANNULE: 'Annulé',
      TERMINE: 'Terminé',
    }
    return labels[formTargetStatus.value] ?? formTargetStatus.value
  })

  // -----------------------------------------------------------------------
  // Watchers internes
  // -----------------------------------------------------------------------
  watch(isSection1Complete, (complete) => {
    if (complete) activeSections.value.add('creneaux')
  })

  watch(
    () => slotsForm.value.length,
    (len) => {
      slotPickers.value = Array.from(
        { length: len },
        (_, i) => slotPickers.value[i] ?? defaultPicker(),
      )
      if (len > 0) activeSections.value.add('equipe')
    },
  )

  // -----------------------------------------------------------------------
  // Click-outside — ferme le dropdown statut cible du formulaire
  // -----------------------------------------------------------------------
  const _onFormStatusClickOutside = (e: MouseEvent) => {
    if (formStatusDropdownRef.value && !formStatusDropdownRef.value.contains(e.target as Node)) {
      formStatusDropdownOpen.value = false
    }
  }
  onMounted(() => document.addEventListener('mousedown', _onFormStatusClickOutside))
  onUnmounted(() => document.removeEventListener('mousedown', _onFormStatusClickOutside))

  // -----------------------------------------------------------------------
  // Fonctions formulaire
  // -----------------------------------------------------------------------
  function toggleSection(id: string): void {
    if (activeSections.value.has(id)) {
      activeSections.value.delete(id)
    } else {
      activeSections.value.add(id)
    }
  }

  function selectMinistere(id: string): void {
    activiteForm.ministere_organisateur_id = id
  }

  function onDateDebutChange(): void {
    if (
      activiteForm.date_fin &&
      new Date(activiteForm.date_fin) <= new Date(activiteForm.date_debut)
    ) {
      activiteForm.date_fin = ''
    }
  }

  function addOneHour(hhmm: string, cap: string): string {
    const [h, m] = hhmm.split(':').map(Number)
    const [ch, cm] = cap.split(':').map(Number)
    const newMinutes = (h ?? 0) * 60 + (m ?? 0) + 60
    const capMinutes = (ch ?? 23) * 60 + (cm ?? 59)
    const capped = Math.min(newMinutes, capMinutes)
    const rh = Math.floor(capped / 60) % 24
    const rm = capped % 60
    return `${String(rh).padStart(2, '0')}:${String(rm).padStart(2, '0')}`
  }

  function addSlot(): void {
    const lastSlot = slotsForm.value.at(-1)
    const rawDebut =
      lastSlot?.heure_fin ??
      (activiteForm.date_debut ? activiteForm.date_debut.substring(11, 16) : '09:00')
    const activityEnd = activiteForm.date_fin ? activiteForm.date_fin.substring(11, 16) : '23:59'
    const defaultFin = addOneHour(rawDebut, activityEnd)
    slotsForm.value.push({
      _tempId: newTempId(),
      nom_creneau: '',
      heure_debut: rawDebut,
      heure_fin: defaultFin,
      nb_personnes_requis: 2,
      affectations: [],
    })
  }

  function removeSlot(idx: number): void {
    slotsForm.value.splice(idx, 1)
  }

  function removeAffectation(slotIdx: number, affIdx: number): void {
    slotsForm.value[slotIdx]?.affectations.splice(affIdx, 1)
  }

  function buildSlotDatetime(activityDate: string, time: string): string {
    const datePart = activityDate.split('T')[0]
    return `${datePart}T${time}:00`
  }

  function formatPreviewDate(dt: string): string {
    if (!dt) return ''
    return new Date(dt).toLocaleDateString('fr-FR', {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
    })
  }

  // -----------------------------------------------------------------------
  // Picker membres
  // -----------------------------------------------------------------------
  function pickerMembers(slotIdx: number): TeamMemberRead[] {
    const picker = slotPickers.value[slotIdx]
    if (!picker?.ministereId || !campusTeam.value) return []
    const min = campusTeam.value.ministeres.find((m) => m.id === picker.ministereId)
    if (!min) return []
    const query = picker.memberQuery.toLowerCase()
    const assigned = new Set(slotsForm.value[slotIdx]?.affectations.map((a) => a.membre_id) ?? [])
    return min.membres.filter(
      (m) =>
        !assigned.has(m.id) && (!query || `${m.prenom} ${m.nom}`.toLowerCase().includes(query)),
    )
  }

  function pickerMemberRoles(slotIdx: number): RoleCompetenceRead[] {
    const picker = slotPickers.value[slotIdx]
    if (!picker?.memberId) return []
    if (picker.memberRoles.length > 0) {
      return roles.value.filter((r) => picker.memberRoles.includes(r.code))
    }
    return roles.value
  }

  function selectPickerMember(slotIdx: number, member: TeamMemberRead): void {
    const picker = slotPickers.value[slotIdx]
    if (!picker) return
    picker.memberId = member.id
    picker.memberPrenom = member.prenom
    picker.memberNom = member.nom
    picker.memberRoles = member.roles
    picker.roleCode = member.roles[0] ?? roles.value[0]?.code ?? ''
    picker.memberQuery = `${member.prenom} ${member.nom}`
    picker.showMemberList = false
  }

  function confirmAffectation(slotIdx: number): void {
    const picker = slotPickers.value[slotIdx]
    const slot = slotsForm.value[slotIdx]
    if (!picker?.memberId || !picker.roleCode || !picker.ministereId || !slot) return
    slot.affectations.push({
      _tempId: newTempId(),
      membre_id: picker.memberId,
      membre_prenom: picker.memberPrenom,
      membre_nom: picker.memberNom,
      role_code: picker.roleCode,
      ministere_id: picker.ministereId,
    })
    slotPickers.value[slotIdx] = defaultPicker()
  }

  function resetPicker(slotIdx: number): void {
    slotPickers.value[slotIdx] = defaultPicker()
  }

  function dismissApplyWarnings(): void {
    applyWarningsIndispo.value = []
    applyIgnoredMembres.value = []
    callbacks.onClose()
  }

  function rolesForMembre(membreId: string): RoleCompetenceRead[] {
    if (!campusTeam.value) return roles.value
    for (const min of campusTeam.value.ministeres) {
      const membre = min.membres.find((m) => m.id === membreId)
      if (membre && membre.roles.length > 0) {
        return roles.value.filter((r) => membre.roles.includes(r.code))
      }
    }
    return roles.value
  }

  /**
   * Résout un membre depuis campusTeam à partir de son ID.
   * Retourne null si introuvable.
   */
  function resolveMembre(membreId: string): { prenom: string; nom: string } | null {
    if (!campusTeam.value) return null
    for (const min of campusTeam.value.ministeres) {
      const m = min.membres.find((mb) => mb.id === membreId)
      if (m) return { prenom: m.prenom, nom: m.nom }
    }
    return null
  }

  function applyTemplate(template: PlanningTemplateRead): void {
    // 1. Pré-remplir le type d'activité
    activiteForm.type = template.activite_type

    // 2. Calculer date_fin depuis date_debut + duree_minutes
    if (activiteForm.date_debut) {
      const debut = new Date(activiteForm.date_debut)
      const fin = new Date(debut.getTime() + template.duree_minutes * 60_000)
      activiteForm.date_fin = fin.toISOString().slice(0, 16)
    }

    // 3. Construire les slots depuis les créneaux du template
    const newSlots: SlotFormItem[] = template.slots.map((tplSlot) => {
      const affectations: AffectationFormItem[] = []

      for (const role of tplSlot.roles) {
        for (const membreSuggere of role.membres_suggeres ?? []) {
          const alreadyAdded = affectations.some(
            (a) => a.membre_id === membreSuggere.membre_id && a.role_code === role.role_code,
          )
          if (alreadyAdded) continue

          const resolved = resolveMembre(membreSuggere.membre_id)
          let prenom = ''
          let nom = membreSuggere.membre_nom ?? ''
          if (resolved) {
            prenom = resolved.prenom
            nom = resolved.nom
          } else if (membreSuggere.membre_nom) {
            const parts = membreSuggere.membre_nom.split(' ')
            prenom = parts[0] ?? ''
            nom = parts.slice(1).join(' ')
          }

          affectations.push({
            _tempId: `suggest-${membreSuggere.membre_id}-${role.role_code}-${Date.now()}`,
            membre_id: membreSuggere.membre_id,
            membre_prenom: prenom,
            membre_nom: nom,
            role_code: role.role_code,
            ministere_id: template.ministere_id,
            statut_affectation_code: 'PROPOSE',
          })
        }
      }

      return {
        _tempId: newTempId(),
        nom_creneau: tplSlot.nom_creneau,
        heure_debut: offsetToHHMM(activiteForm.date_debut, tplSlot.offset_debut_minutes),
        heure_fin: offsetToHHMM(activiteForm.date_debut, tplSlot.offset_fin_minutes),
        nb_personnes_requis: tplSlot.nb_personnes_requis,
        affectations,
      }
    })

    slotsForm.value = newSlots
    slotPickers.value = newSlots.map(() => defaultPicker())

    // 4. Mémoriser la sélection
    selectedTemplateId.value = template.id
    templateApplied.value = true
  }

  // -----------------------------------------------------------------------
  // initForm — réinitialise ou pré-remplit pour create / edit
  // -----------------------------------------------------------------------
  async function initForm(): Promise<void> {
    Object.assign(activiteForm, {
      type: '',
      date_debut: '',
      date_fin: '',
      lieu: '',
      description: '',
      campus_id: '',
      ministere_organisateur_id: '',
    })
    slotsForm.value = []
    slotPickers.value = []
    apiError.value = null
    applyWarningsIndispo.value = []
    applyIgnoredMembres.value = []
    activeSections.value = new Set(['activite'])
    formTargetStatus.value = 'BROUILLON'

    if (internalMode.value === 'edit' && planning.value) {
      const p = planning.value
      const act = p.activite
      if (act) {
        const toLocal = (iso: string) => iso.substring(0, 16)
        activiteForm.type = act.type ?? ''
        activiteForm.date_debut = toLocal(act.date_debut)
        activiteForm.date_fin = act.date_fin ? toLocal(act.date_fin) : ''
        activiteForm.lieu = act.lieu ?? ''
        activiteForm.description = act.description ?? ''
        activiteForm.campus_id = act.campus_id
        activiteForm.ministere_organisateur_id = act.ministere_organisateur_id
      }
      formTargetStatus.value = planning.value.statut_code ?? 'BROUILLON'
      if (activiteForm.campus_id) {
        // preserveMinistere=true : ne pas effacer le ministère déjà sélectionné
        // même s'il n'est pas dans la liste retournée par getCampusTeam
        await loadMinistreresForCampus(activiteForm.campus_id, true)
      }
      slotsForm.value = (p.slots ?? []).map((s) => ({
        _tempId: newTempId(),
        id: s.id,
        nom_creneau: s.nom_creneau,
        heure_debut: s.date_debut.substring(11, 16),
        heure_fin: s.date_fin.substring(11, 16),
        nb_personnes_requis: s.nb_personnes_requis,
        affectations: (s.affectations ?? [])
          .filter((a) => a.membre)
          .map((a) => ({
            _tempId: newTempId(),
            id: a.id,
            membre_id: a.membre!.id,
            membre_prenom: a.membre!.prenom,
            membre_nom: a.membre!.nom,
            role_code: a.role_code,
            ministere_id: findMinistreForMembreInTeam(campusTeam.value, a.membre!.id),
            statut_affectation_code: a.statut_affectation_code as AffectationStatus | undefined,
          })),
      }))
    } else {
      selectedTemplateId.value = null
      templateApplied.value = false
      if (prefillDate.value) {
        activiteForm.date_debut = prefillDate.value.substring(0, 16)
      }
      activiteForm.campus_id = userCampusPrincipalId.value ?? userCampuses.value[0]?.id ?? ''
      if (activiteForm.campus_id) {
        await loadMinistreresForCampus(activiteForm.campus_id)
      }
    }
  }

  // -----------------------------------------------------------------------
  // save — create ou edit
  // -----------------------------------------------------------------------
  async function save(): Promise<void> {
    if (!canSave.value || isSaving.value) return
    isSaving.value = true
    apiError.value = null
    const targetStatus = formTargetStatus.value

    try {
      let result: PlanningFullRead

      const slotsPayload = slotsForm.value.map((slot) => ({
        ...(slot.id ? { id: slot.id } : {}),
        nom_creneau: slot.nom_creneau || 'Créneau',
        date_debut: buildSlotDatetime(activiteForm.date_debut, slot.heure_debut),
        date_fin: buildSlotDatetime(activiteForm.date_debut, slot.heure_fin),
        nb_personnes_requis: slot.nb_personnes_requis,
        affectations: slot.affectations.map((a) => ({
          ...(a.id ? { id: a.id } : {}),
          membre_id: a.membre_id,
          role_code: a.role_code,
          ...(a.ministere_id ? { ministere_id: a.ministere_id } : {}),
        })),
      }))

      if (internalMode.value === 'edit' && planning.value?.id) {
        result = await repo.updateFull(planning.value.id, {
          activite: {
            type: activiteForm.type,
            date_debut: `${activiteForm.date_debut}:00`,
            date_fin: `${activiteForm.date_fin}:00`,
            lieu: activiteForm.lieu || undefined,
            description: activiteForm.description || undefined,
            campus_id: activiteForm.campus_id,
            ministere_organisateur_id: activiteForm.ministere_organisateur_id,
          },
          slots: slotsPayload as never,
        })
      } else {
        result = await repo.createFull({
          activite: {
            type: activiteForm.type,
            date_debut: `${activiteForm.date_debut}:00`,
            date_fin: `${activiteForm.date_fin}:00`,
            lieu: activiteForm.lieu || undefined,
            description: activiteForm.description || undefined,
            campus_id: activiteForm.campus_id,
            ministere_organisateur_id: activiteForm.ministere_organisateur_id,
          },
          slots: slotsPayload as never,
          template_id: selectedTemplateId.value ?? undefined,
        })
      }

      if (targetStatus !== result.statut_code) {
        result = await repo.updateStatus(result.id, targetStatus)
      }

      // US-96 : application des membres suggérés du template sur le planning créé
      if (internalMode.value === 'create' && selectedTemplateId.value) {
        try {
          const applyResult: ApplyTemplateResult = await repo.applyTemplate(
            selectedTemplateId.value,
            result.id,
          )
          applyWarningsIndispo.value = applyResult.avertissements_indispo
          applyIgnoredMembres.value = applyResult.membres_ignores
        } catch {
          // Non bloquant — le planning est créé, les affectations seront à faire manuellement
        }
      }

      const isNew = internalMode.value === 'create'
      notify.success(isNew ? 'Planning créé' : 'Planning mis à jour', result.activite?.type ?? '')
      callbacks.onSaved(result, isNew)
      const hasWarnings =
        applyWarningsIndispo.value.length > 0 || applyIgnoredMembres.value.length > 0
      if (!hasWarnings) {
        callbacks.onClose()
      }
    } catch (e) {
      apiError.value = handleError(e, 'Une erreur est survenue, veuillez réessayer.')
    } finally {
      isSaving.value = false
    }
  }

  return {
    // Mode courant — exposé pour que PlanningFormView puisse conditionner l'affichage
    internalMode,
    // Campus / rôles — exposés pour le shell (partagés avec le mode détail)
    campusTeam,
    campusMinisteres,
    campusMinistereColorMap,
    isLoadingMinisteres,
    roles,
    loadMinistreresForCampus,
    loadRoles,
    // Form state
    activeSections,
    activiteForm,
    slotsForm,
    slotPickers,
    selectedTemplateId,
    templateApplied,
    applyWarningsIndispo,
    applyIgnoredMembres,
    isSaving,
    apiError,
    formTargetStatus,
    formStatusDropdownOpen,
    formStatusDropdownRef,
    // Computed
    selectedMinistereColor,
    dateError,
    isSection1Complete,
    totalAffectations,
    canSave,
    formStatusOptions,
    formStatusLabel,
    // Functions
    toggleSection,
    selectMinistere,
    onDateDebutChange,
    addSlot,
    removeSlot,
    removeAffectation,
    formatPreviewDate,
    pickerMembers,
    pickerMemberRoles,
    selectPickerMember,
    confirmAffectation,
    resetPicker,
    rolesForMembre,
    applyTemplate,
    dismissApplyWarnings,
    initForm,
    save,
  }
}

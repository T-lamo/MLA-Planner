import { ref, computed, onUnmounted } from 'vue'
import type { ProfilCreateFull } from '~~/layers/base/types/profiles'

const DRAFT_KEY = 'mla_profile_draft'

function _hasContent(form: ProfilCreateFull): boolean {
  return !!(
    form.nom?.trim() ||
    form.prenom?.trim() ||
    form.email?.trim() ||
    (form.campus_ids?.length ?? 0) > 0 ||
    (form.ministere_ids?.length ?? 0) > 0 ||
    (form.role_codes?.length ?? 0) > 0
  )
}

function _readStorage(): ProfilCreateFull | null {
  try {
    const raw = localStorage.getItem(DRAFT_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    if (typeof parsed !== 'object' || parsed === null) return null
    return parsed as ProfilCreateFull
  } catch {
    return null
  }
}

export function useDraftProfile() {
  let _timer: ReturnType<typeof setTimeout> | null = null

  const draft = ref<ProfilCreateFull | null>(typeof window !== 'undefined' ? _readStorage() : null)

  onUnmounted(() => {
    if (_timer) clearTimeout(_timer)
  })

  function saveDraft(form: ProfilCreateFull): void {
    if (!_hasContent(form)) return
    if (_timer) clearTimeout(_timer)
    _timer = setTimeout(() => {
      try {
        // Le mot de passe n'est jamais persisté en localStorage
        const toStore: ProfilCreateFull = {
          ...form,
          utilisateur: form.utilisateur ? { ...form.utilisateur, password: '' } : form.utilisateur,
        }
        localStorage.setItem(DRAFT_KEY, JSON.stringify(toStore))
        draft.value = toStore
      } catch {
        // localStorage indisponible (navigation privée, quota) — fail silently
      }
    }, 500)
  }

  function restoreDraft(): ProfilCreateFull | null {
    const saved = _readStorage()
    draft.value = saved
    return saved
  }

  function clearDraft(): void {
    if (_timer) clearTimeout(_timer)
    try {
      localStorage.removeItem(DRAFT_KEY)
    } catch {
      // fail silently
    }
    draft.value = null
  }

  const hasDraft = computed(() => {
    const d = draft.value
    return d !== null && _hasContent(d)
  })

  return { draft, saveDraft, restoreDraft, clearDraft, hasDraft }
}

import type { EnhancedApiError } from '../../types/api'

const lastErrorFingerprint = ref<string | null>(null)
const LOCK_DURATION = 2000

export const useErrorHandler = () => {
  const notify = useMLANotify()

  const notifyError = (error: EnhancedApiError) => {
    // 1. Extraction du code HTTP réel (le nombre 401, 422, etc.)
    const httpStatus = error?.statusCode

    // 2. Extraction des données métier
    const data = error?.data

    // On normalise l'accès : soit data.error (imbriqué), soit data (plat)
    const apiError = data?.error || data

    const message = apiError?.message || apiError?.detail
    const bizCode = apiError?.code // ex: "AUTH_001"

    // --- STRATÉGIE DE DÉDOUBLAGE ---
    const fingerprint = `${httpStatus}-${bizCode || message || 'network'}`
    if (lastErrorFingerprint.value === fingerprint) return
    lastErrorFingerprint.value = fingerprint
    setTimeout(() => {
      lastErrorFingerprint.value = null
    }, LOCK_DURATION)

    // --- LOGIQUE DE ROUTAGE DES NOTIFICATIONS ---

    // Cas 422 : Validation de formulaire
    if (httpStatus === 422) {
      notify.error(
        'Données invalides',
        'Veuillez vérifier les informations saisies dans le formulaire.',
      )
      return
    }

    // Cas 500+ : Erreur Serveur
    if (httpStatus && httpStatus >= 500) {
      notify.error(
        'Erreur Serveur',
        'Service momentanément indisponible. Nos équipes sont sur le coup.',
      )
      return
    }

    // Cas Métier (401, 403, 400, etc.)
    if (message) {
      notify.error(bizCode ? `Erreur : ${bizCode}` : 'Action impossible', message)
      return
    }

    // Cas par défaut : Panne réseau totale ou pas de réponse
    notify.error(
      'Erreur de connexion',
      'Impossible de contacter le serveur. Vérifiez votre connexion internet.',
    )
  }

  return { notifyError }
}

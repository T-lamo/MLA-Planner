import { computed, type Ref } from 'vue'
import type { GenerateSeriesForm } from '../types/planning.types'

const JOURS = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
const ORDINALS = ['1er', '2ème', '3ème', '4ème', '5ème']

export function useSerieDate(form: GenerateSeriesForm | Ref<GenerateSeriesForm>) {
  const f =
    'value' in (form as object)
      ? (form as Ref<GenerateSeriesForm>)
      : { value: form as GenerateSeriesForm }

  const mensuelleLabel = computed((): string => {
    if (!f.value.date_debut || f.value.recurrence !== 'MENSUELLE') return ''
    const d = new Date(f.value.date_debut)
    const weekday = JOURS[(d.getDay() + 6) % 7]
    const n = Math.ceil(d.getDate() / 7)
    const ordinal = ORDINALS[n - 1] ?? `${n}ème`
    return `Chaque ${ordinal} ${weekday} du mois`
  })

  function formatSerieDate(iso: string): string {
    const d = new Date(iso)
    return new Intl.DateTimeFormat('fr-FR', {
      weekday: 'long',
      day: 'numeric',
      month: 'short',
    }).format(d)
  }

  function semaineNum(iso: string): number {
    const d = new Date(iso)
    const start = new Date(d.getFullYear(), 0, 1)
    return Math.ceil(((d.getTime() - start.getTime()) / 86400000 + start.getDay() + 1) / 7)
  }

  return { mensuelleLabel, formatSerieDate, semaineNum }
}

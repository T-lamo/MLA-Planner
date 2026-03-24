<script setup lang="ts">
import type { GenerateSeriesForm, SerieRecurrence } from '../../types/planning.types'
import { useSerieDate } from '../../composables/useSerieDate'

const props = defineProps<{ form: GenerateSeriesForm }>()

const emit = defineEmits<{
  'update:form': [patch: Partial<GenerateSeriesForm>]
}>()

const { mensuelleLabel } = useSerieDate(props.form)

const JOURS_SEMAINE = [
  { value: 0, label: 'Lundi' },
  { value: 1, label: 'Mardi' },
  { value: 2, label: 'Mercredi' },
  { value: 3, label: 'Jeudi' },
  { value: 4, label: 'Vendredi' },
  { value: 5, label: 'Samedi' },
  { value: 6, label: 'Dimanche' },
]

function set(patch: Partial<GenerateSeriesForm>) {
  emit('update:form', patch)
}
</script>

<template>
  <div class="space-y-4">
    <!-- Date début -->
    <div>
      <label class="mb-1 block text-sm font-medium text-(--color-neutral-700)">
        Date de début
      </label>
      <input
        :value="form.date_debut"
        type="date"
        class="w-full rounded-lg border border-(--color-neutral-300) px-3 py-2 text-sm outline-none focus:border-(--color-primary-500)"
        @input="set({ date_debut: ($event.target as HTMLInputElement).value })"
      />
    </div>

    <!-- Date fin -->
    <div>
      <label class="mb-1 block text-sm font-medium text-(--color-neutral-700)"> Date de fin </label>
      <input
        :value="form.date_fin"
        type="date"
        class="w-full rounded-lg border border-(--color-neutral-300) px-3 py-2 text-sm outline-none focus:border-(--color-primary-500)"
        @input="set({ date_fin: ($event.target as HTMLInputElement).value })"
      />
    </div>

    <!-- Récurrence -->
    <div>
      <label class="mb-1 block text-sm font-medium text-(--color-neutral-700)"> Récurrence </label>
      <select
        :value="form.recurrence"
        class="w-full rounded-lg border border-(--color-neutral-300) px-3 py-2 text-sm outline-none focus:border-(--color-primary-500)"
        @change="set({ recurrence: ($event.target as HTMLSelectElement).value as SerieRecurrence })"
      >
        <option value="HEBDOMADAIRE">Hebdomadaire</option>
        <option value="MENSUELLE">Mensuelle</option>
      </select>
    </div>

    <!-- Jour de la semaine (HEBDOMADAIRE uniquement) -->
    <div v-if="form.recurrence === 'HEBDOMADAIRE'">
      <label class="mb-1 block text-sm font-medium text-(--color-neutral-700)">
        Jour de la semaine
      </label>
      <select
        :value="form.jour_semaine ?? 1"
        class="w-full rounded-lg border border-(--color-neutral-300) px-3 py-2 text-sm outline-none focus:border-(--color-primary-500)"
        @change="set({ jour_semaine: Number(($event.target as HTMLSelectElement).value) })"
      >
        <option v-for="j in JOURS_SEMAINE" :key="j.value" :value="j.value">
          {{ j.label }}
        </option>
      </select>
    </div>

    <!-- Info MENSUELLE -->
    <p
      v-if="form.recurrence === 'MENSUELLE' && mensuelleLabel"
      class="rounded-lg bg-(--color-primary-50) px-3 py-2 text-sm text-(--color-primary-700)"
    >
      {{ mensuelleLabel }}
    </p>
  </div>
</template>

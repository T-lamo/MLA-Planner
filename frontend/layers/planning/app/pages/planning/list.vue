<template>
  <div class="rounded-xl border border-slate-200 bg-white shadow-sm">
    <table class="w-full text-left text-sm">
      <thead class="bg-slate-50 text-xs font-bold text-slate-500 uppercase">
        <tr>
          <th class="px-6 py-4">Activité / Date</th>
          <th class="px-6 py-4">Campus</th>
          <th class="px-6 py-4">Statut</th>
          <th class="px-6 py-4">Slots</th>
          <th class="px-6 py-4 text-right">Actions</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-100">
        <tr
          v-for="p in plannings"
          :key="p.id"
          class="cursor-pointer transition hover:bg-(--color-slate-50)"
        >
          <td class="px-6 py-4 font-medium">
            <div class="flex flex-col">
              <span>{{ p.title }}</span>
              <span class="text-xs font-normal text-slate-400">{{ p.date }}</span>
            </div>
          </td>
          <td class="px-6 py-4 text-slate-600">{{ p.campus }}</td>
          <td class="px-6 py-4">
            <!-- <span :class="statusStyles[p.status]" class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium">
              {{ p.status }}
            </span> -->
          </td>
          <td class="px-6 py-4 text-slate-500">{{ p.slotsCount }} slots</td>
          <td class="px-6 py-4 text-right">
            <button class="p-1 hover:text-(--color-primary-600)">
              <MoreVertical class="size-4" />
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { MoreVertical } from 'lucide-vue-next'

const _statusStyles = {
  BROUILLON: 'bg-amber-100 text-amber-700',
  VALIDÉ: 'bg-emerald-100 text-emerald-700',
  ARCHIVÉ: 'bg-slate-100 text-slate-600',
}

const plannings = ref([
  {
    id: 1,
    title: 'Culte de Louange',
    date: '24 Mars 2024',
    campus: 'Paris',
    status: 'BROUILLON',
    slotsCount: 12,
  },
  {
    id: 2,
    title: 'Répétition Générale',
    date: '22 Mars 2024',
    campus: 'Paris',
    status: 'VALIDÉ',
    slotsCount: 8,
  },
])
</script>

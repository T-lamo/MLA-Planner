<script setup lang="ts">
import { Edit2, Trash2, Mail } from 'lucide-vue-next'
import type { ProfilReadFull } from '~~/layers/base/types/profiles'

defineProps<{
  profile: ProfilReadFull
}>()

defineEmits(['edit', 'delete'])
</script>

<template>
  <div
    class="group relative flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-3 transition-all hover:border-(--color-primary-600) hover:shadow-sm"
  >
    <div
      class="flex size-10 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-xs font-bold text-slate-600 transition-colors group-hover:bg-(--color-primary-50) group-hover:text-(--color-primary-600)"
    >
      {{ profile.nom[0] }}{{ profile.prenom[0] }}
    </div>

    <div class="min-w-0 flex-1">
      <div class="flex items-center gap-2">
        <h3 class="truncate text-sm leading-none font-bold text-slate-900">
          {{ profile.nom }} {{ profile.prenom }}
        </h3>
        <span
          :class="['size-1.5 shrink-0 rounded-full', profile.actif ? 'bg-green-500' : 'bg-red-400']"
        />
      </div>

      <div class="mt-1 flex items-center gap-2 text-[11px] text-slate-500">
        <Mail class="size-3" />
        <span class="truncate">{{ profile.email }}</span>
      </div>

      <div class="mt-1.5 flex flex-wrap gap-1">
        <span
          v-for="role in profile.roles_assoc.slice(0, 2)"
          :key="role.role_code"
          class="rounded-md border border-slate-100 bg-slate-50 px-1.5 py-0.5 text-[9px] font-medium text-slate-500"
        >
          {{ role.role_code }}
        </span>
        <span v-if="profile.roles_assoc.length > 2" class="text-[9px] font-medium text-slate-400">
          +{{ profile.roles_assoc.length - 2 }}
        </span>
      </div>
    </div>

    <div
      class="absolute top-1/2 right-2 flex -translate-y-1/2 gap-1 rounded-lg border border-slate-100 bg-white/90 p-1 opacity-0 shadow-sm backdrop-blur-sm transition-opacity group-hover:opacity-100"
    >
      <button
        class="rounded-md p-1.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-900"
        @click="$emit('edit', profile)"
      >
        <Edit2 class="size-3.5" />
      </button>
      <button
        class="rounded-md p-1.5 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-600"
        @click="$emit('delete', profile.id)"
      >
        <Trash2 class="size-3.5" />
      </button>
    </div>
  </div>
</template>

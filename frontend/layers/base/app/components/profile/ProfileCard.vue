<script setup lang="ts">
import { Edit2, Mail, Phone, Trash2, UserCheck, UserX } from 'lucide-vue-next'
import type { ProfilReadFull } from '~~/layers/base/types/profiles'
import CanGuard from '../ui/CanGuard.vue'

defineProps<{
  profile: ProfilReadFull
}>()

defineEmits(['edit', 'delete'])
</script>

<template>
  <div
    class="group relative flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-3 transition-all hover:border-(--color-primary-300) hover:shadow-sm"
  >
    <!-- Avatar -->
    <div
      class="mt-0.5 flex size-10 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-xs font-bold text-slate-600 transition-colors group-hover:bg-(--color-primary-50) group-hover:text-(--color-primary-700)"
    >
      {{ profile.nom[0] }}{{ profile.prenom[0] }}
    </div>

    <!-- Content -->
    <div class="min-w-0 flex-1">
      <!-- Name + status dot -->
      <div class="flex items-center gap-2">
        <h3 class="truncate text-sm leading-snug font-bold text-slate-900">
          {{ profile.nom }} {{ profile.prenom }}
        </h3>
        <span
          :class="['size-1.5 shrink-0 rounded-full', profile.actif ? 'bg-green-500' : 'bg-red-400']"
        />
      </div>

      <!-- Email -->
      <div class="mt-0.5 flex items-center gap-1.5 text-[11px] text-slate-500">
        <Mail class="size-3 shrink-0" />
        <span class="truncate">{{ profile.email }}</span>
      </div>

      <!-- Phone -->
      <div
        v-if="profile.telephone"
        class="mt-0.5 flex items-center gap-1.5 text-[11px] text-slate-400"
      >
        <Phone class="size-3 shrink-0" />
        <span>{{ profile.telephone }}</span>
      </div>

      <!-- Ministères chips -->
      <div v-if="profile.ministeres.length > 0" class="mt-1.5 flex flex-wrap gap-1">
        <span
          v-for="min in profile.ministeres.slice(0, 2)"
          :key="min.id"
          class="rounded-full bg-violet-50 px-2 py-0.5 text-[9px] font-medium text-violet-700"
        >
          {{ min.nom }}
        </span>
        <span
          v-if="profile.ministeres.length > 2"
          class="rounded-full bg-slate-100 px-2 py-0.5 text-[9px] font-medium text-slate-500"
        >
          +{{ profile.ministeres.length - 2 }}
        </span>
      </div>

      <!-- Rôles compétences -->
      <div v-else-if="profile.roles_assoc.length > 0" class="mt-1.5 flex flex-wrap gap-1">
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

      <!-- Compte utilisateur badge -->
      <div
        v-if="profile.utilisateur"
        class="mt-1.5 flex items-center gap-1 text-[10px]"
        :class="profile.utilisateur.actif ? 'text-green-600' : 'text-slate-400'"
      >
        <UserCheck v-if="profile.utilisateur.actif" class="size-3" />
        <UserX v-else class="size-3" />
        <span>{{ profile.utilisateur.actif ? 'Compte actif' : 'Compte inactif' }}</span>
      </div>
    </div>

    <!-- Actions granulaires -->
    <CanGuard :capabilities="['MEMBRE_UPDATE', 'MEMBRE_DELETE']">
      <div
        class="absolute top-2 right-2 flex gap-1 rounded-lg border border-slate-100 bg-white/90 p-1 opacity-0 shadow-sm backdrop-blur-sm transition-opacity group-hover:opacity-100"
      >
        <CanGuard capability="MEMBRE_UPDATE">
          <button
            class="rounded-md p-1.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-900"
            @click="$emit('edit', profile)"
          >
            <Edit2 class="size-3.5" />
          </button>
        </CanGuard>
        <CanGuard capability="MEMBRE_DELETE">
          <button
            class="rounded-md p-1.5 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-600"
            @click="$emit('delete', profile.id)"
          >
            <Trash2 class="size-3.5" />
          </button>
        </CanGuard>
      </div>
    </CanGuard>
  </div>
</template>

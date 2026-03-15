<template>
  <div>
    <p v-if="roles.length === 0" class="py-2 text-sm text-slate-400 italic">
      Aucune compétence définie
    </p>
    <div v-else class="flex flex-wrap gap-2">
      <span
        v-for="role in roles"
        :key="role.code"
        class="inline-flex items-center gap-1.5 rounded-full border border-(--color-primary-200) bg-(--color-primary-50) px-3 py-1 text-xs font-medium"
      >
        <span class="font-mono font-bold text-(--color-primary-700) uppercase">{{
          role.code
        }}</span>
        <span class="text-slate-500">— {{ role.libelle }}</span>
        <button
          class="ml-0.5 rounded-full p-0.5 text-(--color-primary-400) transition-colors hover:bg-(--color-primary-100) hover:text-(--color-primary-700)"
          :title="`Modifier ${role.libelle}`"
          type="button"
          @click.stop="emit('edit', props.categorieId, role.code)"
        >
          <Pencil class="size-3" />
        </button>
        <button
          class="ml-0.5 rounded-full p-0.5 text-(--color-primary-400) transition-colors hover:bg-(--color-primary-100) hover:text-(--color-primary-700)"
          :title="`Supprimer ${role.libelle}`"
          type="button"
          @click.stop="handleDelete(role.code)"
        >
          <X class="size-3" />
        </button>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Pencil, X } from 'lucide-vue-next'
import type { RoleCompetenceRead } from '~~/layers/base/types/role-competence'
import { useMLAConfirm } from '../../composables/useMLAConfirm'

const props = defineProps<{
  roles: RoleCompetenceRead[]
  categorieId: string
}>()

const emit = defineEmits<{
  edit: [categorieId: string, roleCode: string]
  delete: [categorieId: string, roleCode: string]
}>()

const { confirm } = useMLAConfirm()

async function handleDelete(roleCode: string): Promise<void> {
  const ok = await confirm(`Supprimer la compétence "${roleCode}" ?`)
  if (!ok) return
  emit('delete', props.categorieId, roleCode)
}
</script>

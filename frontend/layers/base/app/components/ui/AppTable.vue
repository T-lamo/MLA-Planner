<template>
  <div class="overflow-x-auto">
    <table class="data-table">
      <thead>
        <tr>
          <th
            v-for="col in columns"
            :key="col.key"
            :class="[alignClass(col.align, 'th'), col.width]"
          >
            <slot :name="`header-${col.key}`">{{ col.label }}</slot>
          </th>
        </tr>
      </thead>

      <tbody>
        <!-- État chargement : lignes skeleton -->
        <template v-if="loading">
          <tr v-for="n in skeletonRows" :key="`sk-${n}`">
            <td v-for="col in columns" :key="col.key" :data-label="col.label">
              <div class="skeleton h-4 w-full" />
            </td>
          </tr>
        </template>

        <!-- État vide -->
        <tr v-else-if="rows.length === 0">
          <td :colspan="columns.length" class="py-12 text-center text-sm text-slate-400">
            <slot name="empty">{{ emptyLabel }}</slot>
          </td>
        </tr>

        <!-- Données -->
        <template v-else>
          <tr v-for="row in rows" :key="String(row['id'] ?? JSON.stringify(row))">
            <td
              v-for="col in columns"
              :key="col.key"
              :data-label="col.label"
              :class="alignClass(col.align, 'td')"
            >
              <slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]">
                {{ String(row[col.key] ?? '') }}
              </slot>
            </td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    columns: {
      key: string
      label: string
      align?: 'left' | 'center' | 'right'
      width?: string
    }[]
    rows: Record<string, unknown>[]
    loading?: boolean
    emptyLabel?: string
    skeletonRows?: number
  }>(),
  {
    loading: false,
    emptyLabel: 'Aucun résultat',
    skeletonRows: 5,
  },
)

function alignClass(align: 'left' | 'center' | 'right' | undefined, tag: 'th' | 'td'): string {
  if (tag === 'th') {
    if (align === 'center') return 'text-center'
    if (align === 'right') return 'text-right'
    return ''
  }
  if (align === 'center') return 'text-center'
  if (align === 'right') return 'text-right'
  return ''
}
</script>

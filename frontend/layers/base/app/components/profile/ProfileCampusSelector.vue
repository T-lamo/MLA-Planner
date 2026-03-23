<template>
  <section class="space-y-4">
    <!-- <header class="section-header sticky top-0 z-10 bg-white py-2">
      <MapPin class="size-3.5" /><span>Affectation Campus</span>
    </header> -->
    <div ref="containerRef" class="space-y-3">
      <div v-if="modelValue.length > 0" class="flex flex-wrap gap-2">
        <span
          v-for="cId in modelValue.slice(0, 5)"
          :key="cId"
          class="campus-tag"
          :class="{ 'campus-tag--principal': cId === principalId }"
        >
          <Crown
            v-if="modelValue.length > 1"
            class="size-3 cursor-pointer transition-colors"
            :class="cId === principalId ? 'text-amber-500' : 'text-slate-300 hover:text-amber-400'"
            :title="cId === principalId ? 'Campus principal' : 'Définir comme campus principal'"
            @click.stop="emit('set-principal', cId)"
          />
          {{ campuses.find((c) => c.id === cId)?.nom }}
          <X class="size-3 cursor-pointer hover:text-red-500" @click.stop="removeCampus(cId)" />
        </span>
        <span v-if="modelValue.length > 5" class="campus-tag-more"
          >+{{ modelValue.length - 5 }}</span
        >
      </div>

      <div class="relative">
        <div class="input-wrapper">
          <Search class="input-icon" />
          <input
            v-model="search"
            type="text"
            class="input-field with-icon"
            placeholder="Rechercher..."
            @focus="showDropdown = true"
          />
        </div>

        <div
          v-if="showDropdown && filtered.length > 0"
          class="custom-scrollbar absolute z-50 mt-1 max-h-48 w-full overflow-y-auto rounded-xl border border-slate-200 bg-white shadow-xl"
        >
          <div
            v-for="c in filtered"
            :key="c.id"
            class="flex cursor-pointer items-center justify-between px-4 py-2 text-sm hover:bg-slate-50"
            @click="toggle(c.id)"
          >
            <span :class="modelValue.includes(c.id) ? 'text-primary-600 font-bold' : ''">{{
              c.nom
            }}</span>
            <Check v-if="modelValue.includes(c.id)" class="text-primary-600 size-4" />
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Search, Check, X, Crown } from 'lucide-vue-next'
import type { CampusRead } from '~~/layers/base/types/campus'

const props = defineProps<{ campuses: CampusRead[]; principalId?: string | null }>()
const emit = defineEmits<{ 'set-principal': [id: string] }>()
const modelValue = defineModel<string[]>({ default: () => [] })

const search = ref('')
const showDropdown = ref(false)
const containerRef = ref<HTMLElement | null>(null)

const filtered = computed(() =>
  search.value
    ? props.campuses.filter((c) => c.nom.toLowerCase().includes(search.value.toLowerCase()))
    : props.campuses,
)

const toggle = (id: string) => {
  const idx = modelValue.value.indexOf(id)
  if (idx > -1) {
    modelValue.value.splice(idx, 1)
  } else {
    modelValue.value.push(id)
  }
}
const removeCampus = (id: string) => (modelValue.value = modelValue.value.filter((c) => c !== id))

const onClickOutside = (e: MouseEvent) => {
  if (containerRef.value && !containerRef.value.contains(e.target as Node))
    showDropdown.value = false
}
onMounted(() => document.addEventListener('mousedown', onClickOutside))
onUnmounted(() => document.removeEventListener('mousedown', onClickOutside))
</script>
<style scoped>
@reference "../../assets/css/main.css";
.section-header {
  @apply flex items-center gap-2 border-b border-slate-100 pb-1.5 text-[10px] font-black tracking-widest text-slate-400 uppercase;
}
.input-field {
  @apply w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 transition-all outline-none hover:border-slate-300;
}
.input-wrapper {
  @apply relative flex items-center;
}
.input-icon {
  @apply pointer-events-none absolute left-3 size-3.5 text-slate-400;
}
.input-field.with-icon {
  @apply pl-9;
}
.campus-tag {
  @apply flex items-center gap-1.5 rounded-full px-3 py-1 text-[11px] font-bold;
  background-color: color-mix(in srgb, var(--color-primary-600) 10%, white);
  border: 1px solid color-mix(in srgb, var(--color-primary-600) 20%, white);
  color: var(--color-primary-700);
}
.campus-tag-more {
  @apply rounded-full bg-slate-100 px-3 py-1 text-[11px] font-bold text-slate-600;
}
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #e2e8f0;
  border-radius: 10px;
}
</style>

<template>
  <section class="space-y-4">
    <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
      <AppField id="pbi-nom" label="Nom">
        <input
          id="pbi-nom"
          v-model="modelValue.nom"
          type="text"
          required
          class="form-input"
          placeholder="Ex: MARTIN"
        />
      </AppField>
      <AppField id="pbi-prenom" label="Prénom">
        <input
          id="pbi-prenom"
          v-model="modelValue.prenom"
          type="text"
          required
          class="form-input"
          placeholder="Ex: Lucas"
        />
      </AppField>
      <AppField id="pbi-email" label="Email">
        <template #leading-icon>
          <Mail class="size-3.5" />
        </template>
        <input
          id="pbi-email"
          v-model="modelValue.email"
          type="email"
          required
          class="form-input has-leading-icon"
        />
      </AppField>
      <AppField id="pbi-tel" label="Téléphone">
        <template #leading-icon>
          <Phone class="size-3.5" />
        </template>
        <input
          id="pbi-tel"
          v-model="modelValue.telephone"
          type="tel"
          class="form-input has-leading-icon"
        />
      </AppField>
    </div>
    <div
      class="status-toggle-card group cursor-pointer"
      @click="modelValue.actif = !modelValue.actif"
    >
      <div class="flex flex-col">
        <span class="text-xs font-bold text-slate-700">Disponibilité</span>
        <span class="text-[11px] text-slate-500">Visible dans l'annuaire</span>
      </div>
      <button type="button" :class="['toggle-pill', modelValue.actif ? 'active' : '']">
        <span
          :class="['toggle-circle', modelValue.actif ? 'translate-x-5' : 'translate-x-0']"
        ></span>
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { Mail, Phone } from 'lucide-vue-next'
import AppField from '../ui/AppField.vue'
import type { ProfilCreateFull } from '~~/layers/base/types/profiles'
const modelValue = defineModel<ProfilCreateFull>({ required: true })
</script>

<style scoped>
@reference "../../assets/css/main.css";
.status-toggle-card {
  @apply flex items-center justify-between rounded-xl border border-slate-200 bg-white p-3.5;
}
.toggle-pill {
  @apply relative h-5 w-10 rounded-full bg-slate-200 transition-colors;
}
.toggle-pill.active {
  background-color: #10b981;
}
.toggle-circle {
  @apply absolute top-0.5 left-0.5 size-4 rounded-full bg-white transition-transform duration-200;
  box-shadow: 0 1px 3px rgb(0 0 0 / 0.2);
}
</style>

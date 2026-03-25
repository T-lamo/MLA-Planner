<template>
  <form id="planningForm" class="flex flex-col gap-2 pb-10" @submit.prevent>
    <!-- Mini-preview sticky -->
    <div
      v-if="activiteForm.type || activiteForm.date_debut"
      class="sticky top-0 z-10 -mx-1 mb-2 rounded-xl border px-3 py-2"
      :style="{
        backgroundColor: selectedMinistereColor?.light ?? '#F8FAFC',
        borderColor: selectedMinistereColor?.border ?? '#E2E8F0',
      }"
    >
      <div class="flex items-center gap-2">
        <div
          class="size-2.5 shrink-0 rounded-full"
          :style="{ backgroundColor: selectedMinistereColor?.bg ?? '#94A3B8' }"
        ></div>
        <span class="text-xs font-semibold text-slate-700">
          {{ activiteForm.type || 'Activité' }}
        </span>
        <span v-if="activiteForm.date_debut" class="text-xs text-slate-400">
          — {{ formatPreviewDate(activiteForm.date_debut) }}
        </span>
        <span v-if="slotsForm.length > 0" class="ml-auto text-[10px] font-medium text-slate-400">
          {{ slotsForm.length }} créneau{{ slotsForm.length > 1 ? 'x' : '' }}
        </span>
      </div>
    </div>

    <!-- ── Sélecteur de template ────────────────────────────────────── -->
    <div
      v-if="internalMode === 'create' && templateSections.length > 0"
      class="border-primary-200 bg-primary-50 rounded-xl border p-4"
    >
      <div class="mb-2 flex items-center gap-2">
        <BookmarkPlus class="text-primary-600 h-4 w-4" />
        <p class="text-primary-700 text-sm font-semibold">Utiliser un template</p>
        <span
          v-if="templateApplied"
          class="bg-primary-100 text-primary-700 ml-auto rounded-full px-2 py-0.5 text-xs font-medium"
        >
          ✓ Appliqué
        </span>
      </div>

      <select
        class="border-primary-300 focus:border-primary-500 w-full rounded-lg border bg-white px-3 py-2 text-sm focus:outline-none"
        :value="selectedTemplateId ?? ''"
        @change="handleTemplateSelect"
      >
        <option value="">Choisir un template…</option>
        <optgroup v-for="section in templateSections" :key="section.key" :label="section.label">
          <option v-for="tpl in section.items" :key="tpl.id" :value="tpl.id">
            {{ tpl.nom }}{{ tpl.usage_count > 0 ? ` (utilisé ${tpl.usage_count}×)` : '' }}
          </option>
        </optgroup>
      </select>

      <p class="text-primary-600 mt-1.5 text-xs">
        Le type d'activité et les créneaux seront pré-remplis. Tous les champs restent modifiables.
      </p>
    </div>

    <!-- SECTION 1 — ACTIVITÉ -->
    <FormSection
      title="Activité"
      :icon="Calendar"
      :isOpen="activeSections.has('activite')"
      :badge="isSection1Complete ? '✓' : undefined"
      @toggle="toggleSection('activite')"
    >
      <!-- Type d'activité -->
      <div class="mb-4">
        <label class="mb-2 block text-xs font-semibold tracking-wide text-slate-500 uppercase">
          Type d'activité *
        </label>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="t in ACTIVITE_TYPES"
            :key="t"
            type="button"
            class="rounded-full border px-3 py-1 text-xs font-medium transition-all"
            :class="
              activiteForm.type === t
                ? 'border-transparent text-white'
                : 'border-slate-200 text-slate-500 hover:border-slate-300 hover:text-slate-700'
            "
            :style="
              activiteForm.type === t
                ? { backgroundColor: selectedMinistereColor?.bg ?? '#3B82F6' }
                : {}
            "
            @click="activiteForm.type = t"
          >
            {{ t }}
          </button>
        </div>
      </div>

      <!-- Dates -->
      <div class="mb-4 grid grid-cols-2 gap-3">
        <div>
          <label class="mb-1.5 block text-xs font-semibold tracking-wide text-slate-500 uppercase"
            >Début *</label
          >
          <input
            :value="dateDebutDate"
            type="date"
            :min="todayDate"
            class="mb-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 focus:border-blue-400 focus:outline-none"
            @change="setDebutDate(($event.target as HTMLInputElement).value)"
          />
          <input
            :value="dateDebutTime"
            type="time"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 focus:border-blue-400 focus:outline-none"
            @change="setDebutTime(($event.target as HTMLInputElement).value)"
          />
        </div>
        <div>
          <label class="mb-1.5 block text-xs font-semibold tracking-wide text-slate-500 uppercase"
            >Fin *</label
          >
          <input
            :value="dateFinDate"
            type="date"
            class="mb-1 w-full rounded-lg border px-3 py-2 text-sm text-slate-700 focus:border-blue-400 focus:outline-none"
            :class="dateError ? 'border-red-300 bg-red-50' : 'border-slate-200'"
            :min="dateDebutDate"
            @change="setFinDate(($event.target as HTMLInputElement).value)"
          />
          <input
            :value="dateFinTime"
            type="time"
            class="w-full rounded-lg border px-3 py-2 text-sm text-slate-700 focus:border-blue-400 focus:outline-none"
            :class="dateError ? 'border-red-300 bg-red-50' : 'border-slate-200'"
            @change="setFinTime(($event.target as HTMLInputElement).value)"
          />
          <p v-if="dateError" class="mt-1 text-xs text-red-500">{{ dateError }}</p>
        </div>
      </div>

      <!-- Lieu -->
      <div class="mb-4">
        <label class="mb-1.5 block text-xs font-semibold tracking-wide text-slate-500 uppercase"
          >Lieu</label
        >
        <input
          v-model="activiteForm.lieu"
          type="text"
          placeholder="Ex : Salle principale, Auditorium..."
          class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 placeholder:text-slate-300 focus:border-blue-400 focus:outline-none"
        />
      </div>

      <!-- Campus -->
      <div class="mb-4">
        <label class="mb-2 block text-xs font-semibold tracking-wide text-slate-500 uppercase"
          >Campus *</label
        >
        <div v-if="userCampuses.length > 0" class="flex flex-wrap gap-2">
          <button
            v-for="c in userCampuses"
            :key="c.id"
            type="button"
            class="flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition-all"
            :class="
              activiteForm.campus_id === c.id
                ? 'border-primary-300 bg-primary-50 text-primary-700'
                : userCampuses.length === 1
                  ? 'cursor-default border-slate-200 bg-slate-50 text-slate-600'
                  : 'border-slate-200 bg-slate-50 text-slate-500 hover:border-slate-300 hover:text-slate-700'
            "
            :disabled="userCampuses.length === 1"
            @click="((activiteForm.campus_id = c.id), loadMinistreresForCampus(c.id))"
          >
            <MapPin class="size-3 shrink-0" />
            {{ c.nom }}
          </button>
        </div>
        <p v-else class="text-xs text-slate-400 italic">Aucun campus assigné à votre profil.</p>
      </div>

      <!-- Ministère -->
      <div class="mb-4">
        <label class="mb-2 block text-xs font-semibold tracking-wide text-slate-500 uppercase"
          >Ministère *</label
        >
        <p v-if="!activiteForm.campus_id" class="text-xs text-slate-400 italic">
          Sélectionnez d'abord un campus.
        </p>
        <p v-else-if="isLoadingMinisteres" class="text-xs text-slate-400">Chargement...</p>
        <p v-else-if="campusMinisteres.length === 0" class="text-xs text-slate-400 italic">
          Aucun ministère pour ce campus.
        </p>
        <div v-else class="flex flex-wrap gap-2">
          <button
            v-for="m in campusMinisteres"
            :key="m.id"
            type="button"
            class="flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium transition-all"
            :style="
              activiteForm.ministere_organisateur_id === m.id
                ? {
                    backgroundColor: campusMinistereColorMap.get(m.id)?.bg,
                    borderColor: campusMinistereColorMap.get(m.id)?.bg,
                    color: campusMinistereColorMap.get(m.id)?.text,
                  }
                : {
                    borderColor: campusMinistereColorMap.get(m.id)?.border,
                    color: campusMinistereColorMap.get(m.id)?.bg,
                    backgroundColor: campusMinistereColorMap.get(m.id)?.light,
                  }
            "
            @click="selectMinistere(m.id)"
          >
            <span
              class="size-2 rounded-full"
              :style="{ backgroundColor: campusMinistereColorMap.get(m.id)?.bg }"
            ></span>
            {{ m.nom }}
          </button>
        </div>
      </div>

      <!-- Description -->
      <div>
        <label class="mb-1.5 block text-xs font-semibold tracking-wide text-slate-500 uppercase">
          Description
          <span class="font-normal text-slate-400 normal-case">(optionnel)</span>
        </label>
        <textarea
          v-model="activiteForm.description"
          rows="2"
          placeholder="Notes, instructions particulières..."
          class="w-full resize-none rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 placeholder:text-slate-300 focus:border-blue-400 focus:outline-none"
        ></textarea>
      </div>
    </FormSection>

    <!-- SECTION 2 — CRÉNEAUX -->
    <div :class="{ 'pointer-events-none opacity-40': !isSection1Complete }">
      <FormSection
        title="Créneaux"
        :icon="Clock"
        :isOpen="activeSections.has('creneaux')"
        :badge="slotsForm.length > 0 ? slotsForm.length : undefined"
        @toggle="toggleSection('creneaux')"
      >
        <div class="mb-3 flex justify-end">
          <button
            type="button"
            class="flex items-center gap-1.5 rounded-lg border border-dashed border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-500 transition-colors hover:border-slate-400 hover:text-slate-700"
            @click="addSlot"
          >
            <Plus class="size-3.5" />
            Ajouter un créneau
          </button>
        </div>

        <div class="space-y-3">
          <div
            v-for="(slot, si) in slotsForm"
            :key="slot._tempId"
            class="rounded-xl border border-slate-200 bg-slate-50 p-4"
          >
            <div class="mb-3 flex items-center justify-between">
              <span class="text-xs font-bold text-slate-500 uppercase">Créneau {{ si + 1 }}</span>
              <button
                v-if="slotsForm.length > 1"
                type="button"
                class="rounded-full p-1 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-500"
                @click="removeSlot(si)"
              >
                <Trash2 class="size-3.5" />
              </button>
            </div>

            <div class="mb-3">
              <label class="mb-1 block text-xs font-medium text-slate-500">Libellé</label>
              <input
                v-model="slot.nom_creneau"
                type="text"
                placeholder="Ex : Équipe Louange, Accueil..."
                class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-300 focus:border-blue-400 focus:outline-none"
              />
            </div>

            <div class="mb-3 grid grid-cols-2 gap-3">
              <div>
                <label class="mb-1 block text-xs font-medium text-slate-500">Heure début</label>
                <input
                  v-model="slot.heure_debut"
                  type="time"
                  step="60"
                  class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 focus:border-blue-400 focus:outline-none"
                />
              </div>
              <div>
                <label class="mb-1 block text-xs font-medium text-slate-500">Heure fin</label>
                <input
                  v-model="slot.heure_fin"
                  type="time"
                  step="60"
                  class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 focus:border-blue-400 focus:outline-none"
                />
              </div>
            </div>

            <div>
              <label class="mb-1 block text-xs font-medium text-slate-500"
                >Personnes requises</label
              >
              <div class="flex items-center gap-2">
                <button
                  type="button"
                  class="flex size-7 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 transition-colors hover:bg-slate-100 disabled:opacity-40"
                  :disabled="slot.nb_personnes_requis <= 1"
                  @click="slot.nb_personnes_requis--"
                >
                  <Minus class="size-3" />
                </button>
                <span class="w-6 text-center text-sm font-bold text-slate-700">{{
                  slot.nb_personnes_requis
                }}</span>
                <button
                  type="button"
                  class="flex size-7 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 transition-colors hover:bg-slate-100"
                  @click="slot.nb_personnes_requis++"
                >
                  <Plus class="size-3" />
                </button>
              </div>
            </div>

            <!-- ── Équipe assignée (inline dans le créneau) ── -->
            <div class="mt-4 border-t border-slate-200 pt-3">
              <div class="mb-2 flex items-center justify-between">
                <span class="flex items-center gap-1.5 text-xs font-semibold text-slate-500">
                  <UsersIcon class="size-3.5" /> Équipe
                </span>
                <span
                  class="rounded-full px-2 py-0.5 text-[10px] font-bold"
                  :class="
                    slot.affectations.length >= slot.nb_personnes_requis
                      ? 'bg-emerald-100 text-emerald-600'
                      : slot.affectations.length > 0
                        ? 'bg-amber-100 text-amber-600'
                        : 'bg-slate-100 text-slate-400'
                  "
                >
                  {{ slot.affectations.length }}/{{ slot.nb_personnes_requis }}
                </span>
              </div>

              <div class="mb-2 space-y-2">
                <div
                  v-for="(aff, ai) in slot.affectations"
                  :key="aff._tempId"
                  class="flex items-center gap-2"
                >
                  <div
                    class="flex size-7 shrink-0 items-center justify-center rounded-full text-[10px] font-bold text-white"
                    :style="{ backgroundColor: selectedMinistereColor?.bg ?? '#94A3B8' }"
                  >
                    {{ aff.membre_prenom[0] }}{{ aff.membre_nom[0] }}
                  </div>
                  <span class="flex-1 text-xs font-medium text-slate-700">
                    {{ aff.membre_prenom }} {{ aff.membre_nom }}
                  </span>
                  <select
                    v-model="aff.role_code"
                    class="rounded-md border border-slate-200 bg-white px-2 py-1 text-xs text-slate-600 focus:border-blue-400 focus:outline-none"
                  >
                    <option value="" disabled>Rôle...</option>
                    <option
                      v-for="role in rolesForMembre(aff.membre_id)"
                      :key="role.code"
                      :value="role.code"
                    >
                      {{ role.libelle }}
                    </option>
                  </select>
                  <span
                    v-if="aff.statut_affectation_code && formTargetStatus !== 'PUBLIE'"
                    class="shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-semibold"
                    :class="{
                      'bg-amber-100 text-amber-700': aff.statut_affectation_code === 'PROPOSE',
                      'bg-emerald-100 text-emerald-700': aff.statut_affectation_code === 'CONFIRME',
                      'bg-rose-100 text-rose-700': aff.statut_affectation_code === 'REFUSE',
                      'bg-blue-100 text-blue-700': aff.statut_affectation_code === 'PRESENT',
                      'bg-slate-100 text-slate-500': aff.statut_affectation_code === 'ABSENT',
                      'bg-orange-100 text-orange-700': aff.statut_affectation_code === 'RETARD',
                    }"
                    >{{ aff.statut_affectation_code }}</span
                  >
                  <select
                    v-if="aff.id && formTargetStatus === 'PUBLIE'"
                    v-model="aff.statut_affectation_code"
                    class="shrink-0 rounded-md border border-slate-200 bg-white px-1.5 py-1 text-[10px] text-slate-600 focus:border-blue-400 focus:outline-none"
                    @change="handleStatusChange(aff.id!, aff.statut_affectation_code!)"
                  >
                    <option value="PROPOSE">En attente</option>
                    <option value="CONFIRME">Confirmé</option>
                    <option value="REFUSE">Refusé</option>
                    <option value="PRESENT">Présent</option>
                    <option value="ABSENT">Absent</option>
                    <option value="RETARD">En retard</option>
                  </select>
                  <button
                    type="button"
                    class="shrink-0 rounded-full p-1 text-slate-300 transition-colors hover:bg-red-50 hover:text-red-400"
                    @click="removeAffectation(si, ai)"
                  >
                    <X class="size-3" />
                  </button>
                </div>
              </div>

              <!-- Picker multi-ministère -->
              <div v-if="slotPickers[si]">
                <button
                  v-if="!slotPickers[si].open"
                  type="button"
                  class="w-full rounded-lg border border-dashed border-slate-200 bg-white px-3 py-2 text-xs text-slate-400 transition-colors hover:border-blue-300 hover:text-blue-500"
                  @click="slotPickers[si].open = true"
                >
                  + Ajouter un membre...
                </button>
                <div v-else class="space-y-2 rounded-lg border border-slate-200 bg-white p-2">
                  <div v-if="!slotPickers[si].ministereId">
                    <p
                      class="mb-1 text-[10px] font-semibold tracking-wide text-slate-400 uppercase"
                    >
                      Ministère
                    </p>
                    <div class="flex flex-wrap gap-1">
                      <button
                        v-for="min in campusMinisteres"
                        :key="min.id"
                        type="button"
                        class="rounded-full border px-2 py-0.5 text-xs font-medium transition-colors"
                        :style="{
                          borderColor: campusMinistereColorMap.get(min.id)?.bg ?? '#94A3B8',
                          color: campusMinistereColorMap.get(min.id)?.bg ?? '#94A3B8',
                        }"
                        @click="slotPickers[si].ministereId = min.id"
                      >
                        {{ min.nom }}
                      </button>
                    </div>
                  </div>
                  <template v-else-if="!slotPickers[si].memberId">
                    <div class="mb-1 flex items-center gap-1">
                      <button
                        type="button"
                        class="text-[10px] text-slate-400 hover:text-slate-600"
                        @click="slotPickers[si].ministereId = ''"
                      >
                        ← Retour
                      </button>
                      <span
                        class="ml-1 text-[10px] font-semibold tracking-wide text-slate-400 uppercase"
                      >
                        Membre
                      </span>
                    </div>
                    <input
                      v-model="slotPickers[si].memberQuery"
                      type="text"
                      placeholder="Rechercher..."
                      class="w-full rounded-md border border-slate-200 bg-white px-2 py-1 text-xs focus:border-blue-300 focus:outline-none"
                    />
                    <div class="mt-1 max-h-36 space-y-0.5 overflow-y-auto">
                      <button
                        v-for="membre in pickerMembers(si)"
                        :key="membre.id"
                        type="button"
                        class="flex w-full items-center gap-2 rounded-md px-2 py-1 text-left text-xs hover:bg-slate-50"
                        @click="selectPickerMember(si, membre)"
                      >
                        <div
                          class="flex size-6 shrink-0 items-center justify-center rounded-full text-[9px] font-bold text-white"
                          :style="{
                            backgroundColor:
                              campusMinistereColorMap.get(slotPickers[si].ministereId)?.bg ??
                              '#94A3B8',
                          }"
                        >
                          {{ membre.prenom[0] }}{{ membre.nom[0] }}
                        </div>
                        <span class="font-medium text-slate-700">
                          {{ membre.prenom }} {{ membre.nom }}
                        </span>
                        <span
                          v-if="isMemberUnavailable(membre.id)"
                          class="ml-auto shrink-0 rounded-full bg-amber-100 px-1.5 py-0.5 text-[9px] font-semibold text-amber-700"
                          :title="getWarningTooltip(membre.id)"
                        >
                          ⚠ Indisponible
                        </span>
                      </button>
                      <p
                        v-if="pickerMembers(si).length === 0"
                        class="px-2 py-1 text-xs text-slate-400 italic"
                      >
                        Aucun membre disponible
                      </p>
                    </div>
                  </template>
                  <template v-else>
                    <div class="mb-1 flex items-center gap-1">
                      <button
                        type="button"
                        class="text-[10px] text-slate-400 hover:text-slate-600"
                        @click="slotPickers[si].memberId = ''"
                      >
                        ← Retour
                      </button>
                      <span
                        class="ml-1 text-[10px] font-semibold tracking-wide text-slate-400 uppercase"
                      >
                        Rôle — {{ slotPickers[si].memberPrenom }}
                        {{ slotPickers[si].memberNom }}
                      </span>
                    </div>
                    <select
                      v-model="slotPickers[si].roleCode"
                      class="w-full rounded-md border border-slate-200 bg-white px-2 py-1 text-xs focus:border-blue-300 focus:outline-none"
                    >
                      <option value="" disabled>Choisir un rôle...</option>
                      <option
                        v-for="role in pickerMemberRoles(si)"
                        :key="role.code"
                        :value="role.code"
                      >
                        {{ role.libelle }}
                      </option>
                    </select>
                    <div class="mt-1 flex gap-2">
                      <button
                        type="button"
                        :disabled="!slotPickers[si].roleCode"
                        class="flex-1 rounded-md bg-blue-500 px-3 py-1 text-xs font-medium text-white transition-colors hover:bg-blue-600 disabled:opacity-40"
                        @click="confirmAffectation(si)"
                      >
                        Confirmer
                      </button>
                      <button
                        type="button"
                        class="rounded-md border border-slate-200 px-3 py-1 text-xs text-slate-500 hover:bg-slate-100"
                        @click="resetPicker(si)"
                      >
                        Annuler
                      </button>
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </div>

          <p v-if="slotsForm.length === 0" class="text-sm text-slate-400 italic">
            Ajoutez au moins un créneau pour configurer les affectations.
          </p>
        </div>
      </FormSection>
    </div>

    <!-- ── US-96 : avertissements membres suggérés ──────────────────────── -->
    <div
      v-if="applyWarningsIndispo.length > 0 || applyIgnoredMembres.length > 0"
      class="rounded-xl border border-amber-200 bg-amber-50 p-4"
    >
      <div class="mb-3 flex items-center justify-between">
        <p class="text-sm font-semibold text-amber-800">Avertissements — application du template</p>
        <button
          type="button"
          class="rounded-full p-1 text-amber-500 transition-colors hover:bg-amber-100"
          @click="dismissApplyWarnings()"
        >
          <X class="size-4" />
        </button>
      </div>

      <!-- Indisponibilités -->
      <div v-if="applyWarningsIndispo.length > 0" class="mb-3">
        <div class="mb-1.5 flex items-center gap-1.5">
          <AlertTriangle class="size-3.5 text-amber-600" />
          <p class="text-xs font-semibold text-amber-700">
            Membres indisponibles à cette date ({{ applyWarningsIndispo.length }})
          </p>
        </div>
        <div class="space-y-1">
          <div
            v-for="(w, i) in applyWarningsIndispo"
            :key="i"
            class="flex items-center gap-2 rounded-lg bg-amber-100 px-3 py-1.5 text-xs text-amber-800"
          >
            <span class="font-medium">{{ w.membre_nom }}</span>
            <span class="text-amber-600">·</span>
            <span>{{ w.creneau_nom }}</span>
            <span
              class="ml-auto rounded-full bg-amber-200 px-1.5 py-0.5 font-mono text-[10px] text-amber-700"
            >
              {{ w.role_code }}
            </span>
          </div>
        </div>
      </div>

      <!-- Membres ignorés -->
      <div v-if="applyIgnoredMembres.length > 0">
        <div class="mb-1.5 flex items-center gap-1.5">
          <UserX class="size-3.5 text-slate-500" />
          <p class="text-xs font-semibold text-slate-600">
            Membres ignorés ({{ applyIgnoredMembres.length }})
          </p>
        </div>
        <div class="space-y-1">
          <div
            v-for="(w, i) in applyIgnoredMembres"
            :key="i"
            class="flex items-center gap-2 rounded-lg bg-slate-100 px-3 py-1.5 text-xs text-slate-700"
          >
            <span class="font-medium">{{ w.membre_nom }}</span>
            <span class="text-slate-400">·</span>
            <span
              class="ml-auto rounded-full bg-slate-200 px-1.5 py-0.5 font-mono text-[10px] text-slate-600"
            >
              {{ w.role_code }}
            </span>
            <span
              class="rounded-full px-1.5 py-0.5 text-[10px] font-medium"
              :class="{
                'bg-orange-100 text-orange-700': w.raison === 'hors_ministere',
                'bg-slate-200 text-slate-600': w.raison !== 'hors_ministere',
              }"
            >
              {{ w.raison }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </form>
</template>

<script setup lang="ts">
import { computed, inject, watch } from 'vue'
import {
  X,
  Plus,
  Minus,
  Trash2,
  MapPin,
  Calendar,
  Clock,
  Users as UsersIcon,
  BookmarkPlus,
  AlertTriangle,
  UserX,
} from 'lucide-vue-next'
import FormSection from '~~/layers/base/app/components/FormSection.vue'
import { planningFormKey } from '../composables/usePlanningForm'
import { usePlanningTemplates } from '../composables/usePlanningTemplates'
import { PlanningRepository } from '../repositories/PlanningRepository'
import { ACTIVITE_TYPES } from '../types/planning.types'
import type { AffectationStatus } from '../types/planning.types'
import { useIndisponibiliteWarning } from '../composables/useIndisponibiliteWarning'
import { AffectationRepository } from '../repositories/AffectationRepository'

const affRepo = new AffectationRepository()
const notify = useMLANotify()

async function handleStatusChange(affId: string, newStatus: AffectationStatus) {
  try {
    await affRepo.updateStatus(affId, newStatus)
    notify.success('Statut mis à jour')
  } catch {
    // handled by global fetch interceptor
  }
}

// Destructurer pour bénéficier de l'auto-unwrap des refs dans le template
const form = inject(planningFormKey)!
const {
  activeSections,
  activiteForm,
  slotsForm,
  slotPickers,
  isSection1Complete,
  dateError,
  campusMinisteres,
  campusMinistereColorMap,
  isLoadingMinisteres,
  selectedMinistereColor,
  formTargetStatus,
  selectedTemplateId,
  templateApplied,
  applyWarningsIndispo,
  applyIgnoredMembres,
  toggleSection,
  selectMinistere,
  onDateDebutChange,
  addSlot,
  removeSlot,
  removeAffectation,
  formatPreviewDate,
  pickerMembers,
  pickerMemberRoles,
  selectPickerMember,
  confirmAffectation,
  resetPicker,
  rolesForMembre,
  loadMinistreresForCampus,
  applyTemplate,
  dismissApplyWarnings,
  internalMode,
} = form

// ── Helpers pour séparer date et heure (évite le débordement du datetime-local natif) ──
const todayDate = new Date().toISOString().slice(0, 10)
const dateDebutDate = computed(() => activiteForm.date_debut.slice(0, 10))
const dateDebutTime = computed(() => activiteForm.date_debut.slice(11, 16))
const dateFinDate = computed(() => activiteForm.date_fin.slice(0, 10))
const dateFinTime = computed(() => activiteForm.date_fin.slice(11, 16))

function setDebutDate(d: string) {
  activiteForm.date_debut = d + 'T' + (dateDebutTime.value || '00:00')
  onDateDebutChange()
}
function setDebutTime(t: string) {
  activiteForm.date_debut = (dateDebutDate.value || new Date().toISOString().slice(0, 10)) + 'T' + t
  onDateDebutChange()
}
function setFinDate(d: string) {
  activiteForm.date_fin = d + 'T' + (dateFinTime.value || '00:00')
}
function setFinTime(t: string) {
  activiteForm.date_fin = (dateFinDate.value || new Date().toISOString().slice(0, 10)) + 'T' + t
}

const { templateSections, loadTemplates } = usePlanningTemplates()
const repo = new PlanningRepository()

watch(
  () => activiteForm.campus_id,
  (campusId) => {
    if (campusId) loadTemplates()
  },
  { immediate: true },
)

async function handleTemplateSelect(e: Event): Promise<void> {
  const id = (e.target as HTMLSelectElement).value
  if (!id) return
  const full = await repo.getTemplateFull(id)
  applyTemplate(full)
}

// userCampuses est dans le shell (props) — le form a besoin de la liste pour le template.
// On re-expose via le form composable qui expose campusMinisteres pour les ministères,
// mais userCampuses vient du shell via un prop ou inject supplémentaire.
// Pour l'instant on l'injecte depuis le shell (voir PlanningDetailDrawer.vue).
const userCampuses = inject<Array<{ id: string; nom: string }>>('userCampuses')!

// --- Indisponibilités (soft warning) ---
const { isMemberUnavailable, getWarningTooltip, loadForPeriod } = useIndisponibiliteWarning()

watch(
  () => [activiteForm.campus_id, activiteForm.date_debut, activiteForm.date_fin],
  ([campusId, dateDebut, dateFin]) => {
    if (campusId && dateDebut && dateFin) {
      loadForPeriod(
        campusId as string,
        (dateDebut as string).slice(0, 10),
        (dateFin as string).slice(0, 10),
      )
    }
  },
  { immediate: true },
)
</script>

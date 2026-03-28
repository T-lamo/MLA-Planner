<template>
  <div class="page-wrapper">
    <!-- ── Page Header ── -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Mon Profil</h1>
        <p class="page-subtitle">
          Consultez vos informations personnelles et gérez votre sécurité.
        </p>
      </div>
    </div>

    <!-- ── Skeleton ── -->
    <div v-if="loading" class="layout-grid">
      <div class="space-y-3">
        <div class="skeleton h-72 rounded-2xl" />
        <div class="skeleton h-16 rounded-xl" />
      </div>
      <div class="space-y-4 lg:col-span-2">
        <div class="skeleton h-36 rounded-2xl" />
        <div class="skeleton h-24 rounded-2xl" />
        <div class="skeleton h-28 rounded-2xl" />
        <div class="skeleton h-40 rounded-2xl" />
      </div>
    </div>

    <!-- ── Compte Super Admin ── -->
    <div v-else-if="authStore.isSuperAdmin" class="superadmin-card">
      <div class="superadmin-icon">
        <Shield class="size-8" />
      </div>
      <div class="space-y-1 text-center">
        <p class="text-lg font-bold text-slate-900">Compte Superadministrateur</p>
        <p class="text-sm text-slate-500">Ce compte système n'est lié à aucun profil membre.</p>
      </div>
      <div class="superadmin-info">
        <div class="readonly-field">
          <User class="size-3.5 shrink-0 text-slate-400" />
          <span class="text-sm font-medium text-slate-700">
            {{ authStore.user?.username }}
          </span>
          <span class="readonly-tag">Identifiant système</span>
        </div>
      </div>
      <div class="mt-2 flex flex-wrap justify-center gap-1.5">
        <span
          v-for="role in authStore.user?.roles"
          :key="role"
          :class="['role-badge', roleColor(role)]"
        >
          {{ role }}
        </span>
      </div>

      <!-- Séparateur -->
      <div class="w-full border-t border-slate-100 pt-4">
        <p class="field-label mb-3 text-center">Mot de passe</p>

        <!-- Formulaire changement mot de passe -->
        <form
          v-if="showPasswordForm"
          class="w-full space-y-4"
          @submit.prevent="handleChangePassword"
        >
          <div class="form-group">
            <label>Mot de passe actuel</label>
            <div class="form-input-wrapper">
              <span class="form-input-icon"><Lock class="size-3.5" /></span>
              <input
                v-model="pwForm.current"
                type="password"
                class="form-input has-leading-icon"
                placeholder="••••••••"
                required
              />
            </div>
          </div>

          <div class="form-group">
            <label>Nouveau mot de passe</label>
            <div class="form-input-wrapper">
              <span class="form-input-icon"><Lock class="size-3.5" /></span>
              <input
                v-model="pwForm.next"
                type="password"
                class="form-input has-leading-icon"
                placeholder="Min. 6 caractères"
                minlength="6"
                required
              />
            </div>
            <div v-if="pwForm.next" class="mt-1.5 space-y-1">
              <div class="strength-bar">
                <div :class="['strength-fill', strengthClass]" :style="{ width: strengthWidth }" />
              </div>
              <p :class="['text-[10px] font-semibold', strengthTextClass]">{{ strengthLabel }}</p>
            </div>
          </div>

          <div class="form-group">
            <label>Confirmer le nouveau mot de passe</label>
            <div class="form-input-wrapper">
              <span class="form-input-icon"><Lock class="size-3.5" /></span>
              <input
                v-model="pwForm.confirm"
                type="password"
                class="form-input has-leading-icon"
                :class="{ 'border-red-300': pwForm.confirm && pwForm.next !== pwForm.confirm }"
                placeholder="••••••••"
                required
              />
            </div>
            <p
              v-if="pwForm.confirm && pwForm.next !== pwForm.confirm"
              class="mt-0.5 text-[11px] text-red-500"
            >
              Les mots de passe ne correspondent pas.
            </p>
          </div>

          <div v-if="pwError" class="feedback-box error">
            <AlertCircle class="size-3.5 shrink-0" />
            <span>{{ pwError }}</span>
          </div>
          <div v-if="pwSuccess" class="feedback-box success">
            <CheckCircle2 class="size-3.5 shrink-0" />
            <span>{{ pwSuccess }}</span>
          </div>

          <div class="flex flex-wrap gap-2">
            <button type="submit" :disabled="pwLoading" class="btn btn-primary flex-1 sm:flex-none">
              <span v-if="pwLoading" class="flex items-center gap-1.5">
                <span class="loading-dot" />Enregistrement...
              </span>
              <span v-else>Enregistrer</span>
            </button>
            <button
              type="button"
              class="btn btn-secondary flex-1 sm:flex-none"
              @click="cancelPasswordForm"
            >
              Annuler
            </button>
          </div>
        </form>

        <button
          v-else
          class="btn btn-secondary mx-auto w-full sm:w-auto"
          @click="showPasswordForm = true"
        >
          <KeyRound class="size-3.5" />
          Changer le mot de passe
        </button>
      </div>
    </div>

    <!-- ── Erreur ── -->
    <div v-else-if="error" class="error-box">
      <AlertCircle class="size-5 shrink-0 text-red-400" />
      <div>
        <p class="font-semibold text-red-700">Impossible de charger votre profil.</p>
        <p class="mt-0.5 text-xs text-red-500">
          Vérifiez votre connexion ou contactez un administrateur.
        </p>
      </div>
    </div>

    <!-- ── Contenu ── -->
    <div v-else-if="profile" class="layout-grid">
      <!-- ═══════════════════════════════
           Colonne Gauche — Carte Identité
      ═══════════════════════════════ -->
      <aside class="sticky-aside">
        <!-- Carte principale identité -->
        <div class="identity-card">
          <!-- Avatar -->
          <div class="avatar-ring">
            <div class="avatar">{{ initials }}</div>
          </div>

          <!-- Nom + Username -->
          <div class="space-y-1 text-center">
            <p class="text-xl leading-tight font-bold text-slate-900">
              {{ profile.prenom }} {{ profile.nom }}
            </p>
            <span class="username-pill">@{{ authStore.user?.username }}</span>
          </div>

          <!-- Statut -->
          <div :class="['status-badge', profile.actif ? 'active' : 'inactive']">
            <span :class="['status-dot', profile.actif ? 'dot-active' : 'dot-inactive']" />
            {{ profile.actif ? 'Compte actif' : 'Compte inactif' }}
          </div>

          <!-- Séparateur : Rôles applicatifs -->
          <div v-if="authStore.user?.roles?.length" class="section-divider">
            <span class="divider-label">Rôles applicatifs</span>
            <div class="mt-2.5 flex flex-wrap justify-center gap-1.5">
              <span
                v-for="role in authStore.user.roles"
                :key="role"
                :class="['role-badge', roleColor(role)]"
              >
                {{ role }}
              </span>
            </div>
          </div>

          <!-- Séparateur : Campus principal -->
          <div v-if="principalCampus" class="section-divider">
            <span class="divider-label">Campus principal</span>
            <div class="mt-2.5 flex items-center justify-center gap-2">
              <div class="campus-icon-wrapper">
                <MapPin class="size-3.5" />
              </div>
              <span class="text-sm font-semibold text-slate-700">{{ principalCampus.nom }}</span>
            </div>
          </div>
        </div>
      </aside>

      <!-- ═══════════════════════════════
           Colonne Droite — Sections Info
      ═══════════════════════════════ -->
      <div class="space-y-4 lg:col-span-2">
        <!-- ── Informations personnelles ── -->
        <div class="info-card">
          <div class="card-header">
            <div class="card-icon-box">
              <User class="size-4" />
            </div>
            <h2 class="card-title">Informations personnelles</h2>
            <button
              v-if="!editingInfo"
              type="button"
              class="ml-auto flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-[11px] font-semibold text-slate-600 transition-colors hover:bg-slate-50"
              @click="startEditInfo"
            >
              <Pencil class="size-3" />
              Modifier
            </button>
          </div>
          <div class="card-body">
            <!-- Mode lecture -->
            <div v-if="!editingInfo" class="grid grid-cols-1 gap-5 sm:grid-cols-2">
              <div class="info-field">
                <span class="field-label">Prénom</span>
                <span class="field-value">{{ profile.prenom }}</span>
              </div>
              <div class="info-field">
                <span class="field-label">Nom</span>
                <span class="field-value">{{ profile.nom }}</span>
              </div>
              <div class="info-field">
                <span class="field-label">Email</span>
                <a :href="`mailto:${profile.email}`" class="field-value field-link">
                  {{ profile.email }}
                </a>
              </div>
              <div class="info-field">
                <span class="field-label">Téléphone</span>
                <span class="field-value">{{ profile.telephone || '—' }}</span>
              </div>
            </div>

            <!-- Mode édition -->
            <form v-else class="space-y-4" @submit.prevent="saveEditInfo">
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div class="form-group">
                  <label>Prénom</label>
                  <input v-model="infoForm.prenom" type="text" class="form-input" required />
                </div>
                <div class="form-group">
                  <label>Nom</label>
                  <input v-model="infoForm.nom" type="text" class="form-input" required />
                </div>
                <div class="form-group">
                  <label>Email</label>
                  <input v-model="infoForm.email" type="email" class="form-input" required />
                </div>
                <div class="form-group">
                  <label>Téléphone</label>
                  <input
                    v-model="infoForm.telephone"
                    type="tel"
                    class="form-input"
                    placeholder="Ex: +33 6 00 00 00 00"
                  />
                </div>
              </div>
              <div v-if="infoError" class="feedback-box error">
                <AlertCircle class="size-3.5 shrink-0" />
                <span>{{ infoError }}</span>
              </div>
              <div class="flex gap-2">
                <button type="submit" :disabled="infoLoading" class="btn btn-primary">
                  {{ infoLoading ? 'Enregistrement...' : 'Enregistrer' }}
                </button>
                <button type="button" class="btn btn-secondary" @click="cancelEditInfo">
                  Annuler
                </button>
              </div>
            </form>
          </div>
        </div>

        <!-- ── Campus ── -->
        <div class="info-card">
          <div class="card-header">
            <div class="card-icon-box">
              <MapPin class="size-4" />
            </div>
            <h2 class="card-title">Campus</h2>
          </div>
          <div class="card-body">
            <div v-if="profile.campuses?.length" class="flex flex-wrap gap-2">
              <div
                v-for="campus in profile.campuses"
                :key="campus.id"
                :class="[
                  'campus-chip',
                  campus.id === profile.campus_principal_id ? 'campus-chip-principal' : '',
                ]"
              >
                <MapPin class="size-3 shrink-0" />
                <span>{{ campus.nom }}</span>
                <span v-if="campus.id === profile.campus_principal_id" class="principal-tag">
                  Principal
                </span>
              </div>
            </div>
            <div v-else class="empty-state">
              <MapPin class="size-7 text-slate-200" />
              <p class="text-sm text-slate-400 italic">Aucun campus assigné.</p>
            </div>
            <div class="admin-note">
              <Info class="size-3.5 shrink-0 text-blue-400" />
              <span>Les affectations de campus sont gérées par un administrateur.</span>
            </div>
          </div>
        </div>

        <!-- ── Ministères & Pôles ── -->
        <div class="info-card">
          <div class="card-header">
            <div class="card-icon-box">
              <Building2 class="size-4" />
            </div>
            <h2 class="card-title">Ministères & Pôles</h2>
          </div>
          <div class="card-body">
            <div v-if="profile.ministeres?.length" class="space-y-3">
              <div v-for="min in profile.ministeres" :key="min.id" class="ministere-block">
                <div class="ministere-header">
                  <Building2 class="size-3.5 shrink-0" />
                  <span>{{ min.nom }}</span>
                </div>
                <div
                  v-if="polesForMinistere(min.id).length"
                  class="mt-2 ml-1 flex flex-wrap gap-1.5"
                >
                  <span v-for="pole in polesForMinistere(min.id)" :key="pole.id" class="pole-chip">
                    {{ pole.nom }}
                  </span>
                </div>
              </div>
            </div>
            <div v-else class="empty-state">
              <Building2 class="size-7 text-slate-200" />
              <p class="text-sm text-slate-400 italic">Aucun ministère assigné.</p>
            </div>
            <div class="admin-note">
              <Info class="size-3.5 shrink-0 text-blue-400" />
              <span>Les affectations de ministères sont gérées par un administrateur.</span>
            </div>
          </div>
        </div>

        <!-- ── Sécurité ── -->
        <div class="info-card">
          <div class="card-header">
            <div class="card-icon-box">
              <Shield class="size-4" />
            </div>
            <h2 class="card-title">Sécurité</h2>
          </div>
          <div class="card-body space-y-5">
            <!-- Identifiant -->
            <div>
              <p class="field-label mb-2">Identifiant de connexion</p>
              <div class="readonly-field">
                <User class="size-3.5 shrink-0 text-slate-400" />
                <span class="text-sm font-medium text-slate-700">{{
                  authStore.user?.username
                }}</span>
                <span class="readonly-tag">Non modifiable</span>
              </div>
            </div>

            <!-- Mot de passe -->
            <div class="border-t border-slate-100 pt-5">
              <p class="field-label mb-3">Mot de passe</p>

              <!-- Formulaire -->
              <form
                v-if="showPasswordForm"
                class="space-y-4"
                @submit.prevent="handleChangePassword"
              >
                <div class="form-group">
                  <label>Mot de passe actuel</label>
                  <div class="form-input-wrapper">
                    <span class="form-input-icon"><Lock class="size-3.5" /></span>
                    <input
                      v-model="pwForm.current"
                      type="password"
                      class="form-input has-leading-icon"
                      placeholder="••••••••"
                      required
                    />
                  </div>
                </div>

                <div class="form-group">
                  <label>Nouveau mot de passe</label>
                  <div class="form-input-wrapper">
                    <span class="form-input-icon"><Lock class="size-3.5" /></span>
                    <input
                      v-model="pwForm.next"
                      type="password"
                      class="form-input has-leading-icon"
                      placeholder="Min. 6 caractères"
                      minlength="6"
                      required
                    />
                  </div>
                  <!-- Indicateur de force -->
                  <div v-if="pwForm.next" class="mt-1.5 space-y-1">
                    <div class="strength-bar">
                      <div
                        :class="['strength-fill', strengthClass]"
                        :style="{ width: strengthWidth }"
                      />
                    </div>
                    <p :class="['text-[10px] font-semibold', strengthTextClass]">
                      {{ strengthLabel }}
                    </p>
                  </div>
                </div>

                <div class="form-group">
                  <label>Confirmer le nouveau mot de passe</label>
                  <div class="form-input-wrapper">
                    <span class="form-input-icon"><Lock class="size-3.5" /></span>
                    <input
                      v-model="pwForm.confirm"
                      type="password"
                      class="form-input has-leading-icon"
                      :class="{
                        'border-red-300': pwForm.confirm && pwForm.next !== pwForm.confirm,
                      }"
                      placeholder="••••••••"
                      required
                    />
                  </div>
                  <p
                    v-if="pwForm.confirm && pwForm.next !== pwForm.confirm"
                    class="mt-0.5 text-[11px] text-red-500"
                  >
                    Les mots de passe ne correspondent pas.
                  </p>
                </div>

                <!-- Feedback -->
                <div v-if="pwError" class="feedback-box error">
                  <AlertCircle class="size-3.5 shrink-0" />
                  <span>{{ pwError }}</span>
                </div>
                <div v-if="pwSuccess" class="feedback-box success">
                  <CheckCircle2 class="size-3.5 shrink-0" />
                  <span>{{ pwSuccess }}</span>
                </div>

                <div class="flex gap-2">
                  <button type="submit" :disabled="pwLoading" class="btn btn-primary">
                    <span v-if="pwLoading" class="flex items-center gap-1.5">
                      <span class="loading-dot" />Enregistrement...
                    </span>
                    <span v-else>Enregistrer</span>
                  </button>
                  <button type="button" class="btn btn-secondary" @click="cancelPasswordForm">
                    Annuler
                  </button>
                </div>
              </form>

              <!-- Bouton déclencheur -->
              <button v-else class="btn btn-secondary" @click="showPasswordForm = true">
                <KeyRound class="size-3.5" />
                Changer le mot de passe
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  User,
  MapPin,
  Building2,
  Shield,
  Lock,
  KeyRound,
  AlertCircle,
  CheckCircle2,
  Info,
  Pencil,
} from 'lucide-vue-next'
import { useAuthStore } from '~~/layers/auth/app/stores/useAuthStore'
import { ProfileRepository } from '../../repositories/ProfileRepository'
import type { ProfilReadFull } from '~~/layers/base/types/profiles'
import type { PoleSimple } from '~~/layers/base/types/pole'

const authStore = useAuthStore()
const profileRepo = new ProfileRepository()

const profile = ref<ProfilReadFull | null>(null)
const loading = ref(true)
const error = ref(false)

// Changement de mot de passe
const showPasswordForm = ref(false)
const pwForm = ref({ current: '', next: '', confirm: '' })
const pwLoading = ref(false)
const pwError = ref('')
const pwSuccess = ref('')

onMounted(async () => {
  if (authStore.isSuperAdmin) {
    loading.value = false
    return
  }
  try {
    profile.value = await profileRepo.getMyProfile()
  } catch {
    error.value = true
  } finally {
    loading.value = false
  }
})

// ── Édition infos personnelles ──
const editingInfo = ref(false)
const infoForm = ref({ prenom: '', nom: '', email: '', telephone: '' })
const infoLoading = ref(false)
const infoError = ref('')

const startEditInfo = () => {
  if (!profile.value) return
  infoForm.value = {
    prenom: profile.value.prenom,
    nom: profile.value.nom,
    email: profile.value.email,
    telephone: profile.value.telephone ?? '',
  }
  infoError.value = ''
  editingInfo.value = true
}

const cancelEditInfo = () => {
  editingInfo.value = false
  infoError.value = ''
}

const saveEditInfo = async () => {
  infoError.value = ''
  infoLoading.value = true
  try {
    const updated = await profileRepo.updateMyProfile({
      nom: infoForm.value.nom,
      prenom: infoForm.value.prenom,
      email: infoForm.value.email,
      telephone: infoForm.value.telephone || null,
    })
    profile.value = updated
    editingInfo.value = false
  } catch {
    infoError.value = 'Erreur lors de la mise à jour. Veuillez réessayer.'
  } finally {
    infoLoading.value = false
  }
}

const initials = computed(() => {
  if (!profile.value) return '?'
  return `${profile.value.prenom[0] ?? ''}${profile.value.nom[0] ?? ''}`.toUpperCase()
})

const principalCampus = computed(() =>
  profile.value?.campuses?.find((c) => c.id === profile.value?.campus_principal_id),
)

const polesForMinistere = (ministereId: string) =>
  (profile.value?.poles as PoleSimple[] | undefined)?.filter(
    (p) => p.ministere_id === ministereId,
  ) ?? []

const roleColor = (role: string) => {
  if (role.toLowerCase().includes('super')) return 'role-super'
  if (role.toLowerCase().includes('admin')) return 'role-admin'
  if (role.toLowerCase().includes('responsable')) return 'role-resp'
  return 'role-default'
}

// ── Indicateur de force du mot de passe ──
const passwordStrength = computed(() => {
  const pw = pwForm.value.next
  if (!pw) return 0
  let score = 0
  if (pw.length >= 6) score++
  if (pw.length >= 10) score++
  if (/[A-Z]/.test(pw)) score++
  if (/[0-9]/.test(pw)) score++
  if (/[^A-Za-z0-9]/.test(pw)) score++
  return score
})

const strengthClass = computed(() => {
  const s = passwordStrength.value
  if (s <= 1) return 'fill-weak'
  if (s <= 3) return 'fill-medium'
  return 'fill-strong'
})
const strengthWidth = computed(() => `${Math.min(100, passwordStrength.value * 20)}%`)
const strengthLabel = computed(() => {
  const s = passwordStrength.value
  if (s <= 1) return 'Faible'
  if (s <= 3) return 'Moyen'
  return 'Fort'
})
const strengthTextClass = computed(() => {
  const s = passwordStrength.value
  if (s <= 1) return 'text-red-500'
  if (s <= 3) return 'text-amber-500'
  return 'text-green-600'
})

const cancelPasswordForm = () => {
  showPasswordForm.value = false
  pwForm.value = { current: '', next: '', confirm: '' }
  pwError.value = ''
  pwSuccess.value = ''
}

const handleChangePassword = async () => {
  pwError.value = ''
  pwSuccess.value = ''
  if (pwForm.value.next !== pwForm.value.confirm) {
    pwError.value = 'Les mots de passe ne correspondent pas.'
    return
  }
  if (!authStore.user?.id) return
  pwLoading.value = true
  try {
    await profileRepo.changePassword(authStore.user.id, pwForm.value.current, pwForm.value.next)
    pwSuccess.value = 'Mot de passe modifié avec succès.'
    pwForm.value = { current: '', next: '', confirm: '' }
    setTimeout(() => {
      showPasswordForm.value = false
      pwSuccess.value = ''
    }, 2500)
  } catch {
    pwError.value = 'Mot de passe actuel incorrect ou erreur serveur.'
  } finally {
    pwLoading.value = false
  }
}
</script>

<style scoped>
@reference "../../assets/css/main.css";

/* ══════════════════════════════════════════
   PAGE LAYOUT
══════════════════════════════════════════ */
.page-wrapper {
  @apply mx-auto w-full max-w-5xl space-y-6 p-4 md:p-8;
}

.layout-grid {
  @apply grid grid-cols-1 gap-6 lg:grid-cols-3;
}

/* ── Page Header ── */
.page-header {
  @apply flex items-end justify-between;
}
.page-title {
  @apply text-2xl font-bold text-slate-900;
}
.page-subtitle {
  @apply mt-0.5 text-sm text-slate-500;
}

/* ── Skeleton ── */
.skeleton {
  @apply animate-pulse bg-slate-100;
}

/* ── Error box ── */
.error-box {
  @apply flex items-start gap-3 rounded-2xl border border-red-100 bg-red-50 p-5 text-sm text-red-700;
}

/* ── Super Admin card ── */
.superadmin-card {
  @apply mx-auto flex w-full max-w-md flex-col items-center gap-5 rounded-2xl border border-purple-200/80 bg-white p-5 shadow-sm sm:p-8;
}
.superadmin-icon {
  @apply flex size-14 items-center justify-center rounded-2xl bg-purple-50 sm:size-16;
  color: var(--color-purple-600, #9333ea);
}
.superadmin-info {
  @apply w-full;
}

/* ══════════════════════════════════════════
   COLONNE GAUCHE — CARTE IDENTITÉ
══════════════════════════════════════════ */
.sticky-aside {
  @apply flex flex-col gap-4 lg:sticky lg:top-6 lg:self-start;
}

.identity-card {
  @apply flex flex-col items-center gap-5 rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm;
}

/* ── Avatar ── */
.avatar-ring {
  @apply rounded-full p-1;
  background: linear-gradient(135deg, var(--color-primary-600), var(--color-primary-700));
  box-shadow: 0 4px 20px color-mix(in srgb, var(--color-primary-600) 30%, transparent);
}

.avatar {
  @apply flex size-21 items-center justify-center rounded-full bg-white text-[28px] font-black;
  color: var(--color-primary-600);
  letter-spacing: -0.02em;
}

/* ── Username pill ── */
.username-pill {
  @apply inline-block rounded-full bg-slate-100 px-3 py-0.5 text-xs font-medium text-slate-500;
}

/* ── Statut ── */
.status-badge {
  @apply flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold;
}
.status-badge.active {
  @apply bg-green-50 text-green-700;
}
.status-badge.inactive {
  @apply bg-slate-100 text-slate-500;
}

.status-dot {
  @apply size-1.5 rounded-full;
}
.dot-active {
  @apply bg-green-500;
  box-shadow: 0 0 0 2px rgba(34, 197, 94, 0.25);
  animation: pulse-green 2s ease-in-out infinite;
}
.dot-inactive {
  @apply bg-slate-400;
}

@keyframes pulse-green {
  0%,
  100% {
    box-shadow: 0 0 0 2px rgba(34, 197, 94, 0.25);
  }
  50% {
    box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.1);
  }
}

/* ── Séparateurs de section ── */
.section-divider {
  @apply w-full border-t border-slate-100 pt-4;
}

.divider-label {
  @apply block text-center text-[10px] font-bold tracking-widest text-slate-400 uppercase;
}

/* ── Rôles ── */
.role-badge {
  @apply rounded-full border px-2.5 py-0.5 text-[11px] font-semibold;
}
.role-super {
  @apply border-purple-200 bg-purple-50 text-purple-700;
}
.role-admin {
  @apply border-blue-200 bg-blue-50 text-blue-700;
}
.role-resp {
  @apply border-amber-200 bg-amber-50 text-amber-700;
}
.role-default {
  @apply border-slate-200 bg-slate-50 text-slate-600;
}

/* ── Campus icon ── */
.campus-icon-wrapper {
  @apply flex size-6 items-center justify-center rounded-lg;
  background-color: var(--color-primary-50);
  color: var(--color-primary-600);
}

/* ══════════════════════════════════════════
   INFO CARDS
══════════════════════════════════════════ */
.info-card {
  @apply overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-sm;
}

/* ── Card header ── */
.card-header {
  @apply flex items-center gap-3 border-b border-slate-100 bg-slate-50/70 px-5 py-3.5;
}

.card-icon-box {
  @apply flex size-7 items-center justify-center rounded-lg;
  background-color: var(--color-primary-50);
  color: var(--color-primary-600);
}

.card-title {
  @apply text-[11px] font-bold tracking-widest text-slate-600 uppercase;
}

/* ── Card body ── */
.card-body {
  @apply p-5;
}

/* ── Champs info ── */
.info-field {
  @apply flex flex-col gap-1;
}
.field-label {
  @apply text-[10px] font-bold tracking-widest text-slate-400 uppercase;
}
.field-value {
  @apply text-sm font-medium text-slate-800;
}
.field-link {
  @apply text-primary-600 hover:text-primary-700 underline underline-offset-2 transition-colors;
  text-decoration-style: dotted;
}

/* ── Campus chips ── */
.campus-chip {
  @apply flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700 shadow-[0_1px_3px_rgba(0,0,0,0.05)] transition-shadow hover:shadow-md;
}
.campus-chip-principal {
  border-color: var(--color-primary-200, #bfdbfe);
  background-color: var(--color-primary-50);
  color: var(--color-primary-700, #1d4ed8);
}
.campus-chip svg {
  color: var(--color-primary-500, #3b82f6);
}

.principal-tag {
  @apply rounded-full border px-2 py-0.5 text-[10px] font-bold;
  border-color: var(--color-primary-200, #bfdbfe);
  background-color: var(--color-primary-50);
  color: var(--color-primary-700, #1d4ed8);
}

/* ── Ministère block ── */
.ministere-block {
  @apply rounded-xl border border-slate-100 bg-slate-50/60 p-3;
}
.ministere-header {
  @apply flex items-center gap-2 text-sm font-semibold text-slate-700;
  color: var(--color-primary-700);
}
.ministere-header svg {
  color: var(--color-primary-500, #3b82f6);
}

/* ── Pôles chips ── */
.pole-chip {
  @apply rounded-full border px-2.5 py-0.5 text-xs font-medium;
  border-color: var(--color-primary-100, #dbeafe);
  background-color: var(--color-primary-50);
  color: var(--color-primary-700, #1d4ed8);
}

/* ── Empty state ── */
.empty-state {
  @apply flex flex-col items-center gap-2 py-6 text-center;
}

/* ── Note admin ── */
.admin-note {
  @apply mt-3 flex items-center gap-2 rounded-lg border border-blue-100 bg-blue-50/50 px-3 py-2 text-[11px] text-blue-600;
}

/* ══════════════════════════════════════════
   SECTION SÉCURITÉ
══════════════════════════════════════════ */
.readonly-field {
  @apply flex items-center gap-2.5 rounded-lg border border-dashed border-slate-200 bg-slate-50 px-3 py-2.5;
}
.readonly-tag {
  @apply ml-auto rounded-full bg-slate-200/70 px-2 py-0.5 text-[10px] font-semibold text-slate-500;
}

/* ── Force mot de passe ── */
.strength-bar {
  @apply h-1 w-full overflow-hidden rounded-full bg-slate-100;
}
.strength-fill {
  @apply h-full rounded-full transition-all duration-300;
}
.fill-weak {
  @apply bg-red-400;
}
.fill-medium {
  @apply bg-amber-400;
}
.fill-strong {
  @apply bg-green-500;
}

/* ── Feedback ── */
.feedback-box {
  @apply flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium;
}
.feedback-box.error {
  @apply border border-red-100 bg-red-50 text-red-600;
}
.feedback-box.success {
  @apply border border-green-100 bg-green-50 text-green-700;
}

/* ── Formulaire ── */
.form-group {
  @apply flex flex-col gap-1.5;
}
.form-group label {
  @apply text-[10px] font-bold tracking-widest text-slate-500 uppercase;
}
/* ── Loading dot ── */
.loading-dot {
  @apply size-2 rounded-full bg-white/70;
  animation: blink 1s ease-in-out infinite;
}
@keyframes blink {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
}
</style>

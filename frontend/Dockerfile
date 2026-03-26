# ═══════════════════════════════════════════════════════════════
# Stage 1 — Builder
# Contexte de build : racine du monorepo (mla-app/)
# ═══════════════════════════════════════════════════════════════
FROM node:22-alpine AS builder

WORKDIR /app

# Installer pnpm
RUN npm install -g pnpm

# ── Copier les manifestes du workspace (couche cachée) ─────────
# Séparés des sources pour ne pas invalider le cache pnpm
# quand seul le code source change
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY packages/ui-core/package.json ./packages/ui-core/
COPY frontend/package.json ./frontend/

# ── Installer toutes les dépendances du workspace ─────────────
RUN pnpm install --frozen-lockfile

# ── Copier et builder ui-core (requis par le frontend) ─────────
COPY packages/ui-core ./packages/ui-core
RUN pnpm --filter @shared/ui-core run build

# ── Copier le frontend ─────────────────────────────────────────
COPY frontend ./frontend

# ── URL de l'API — surchargeable à runtime via NUXT_PUBLIC_API_BASE
# Le serveur Nitro lit la variable d'env au démarrage et l'injecte
# dans le HTML rendu pour le navigateur. Pas besoin de rebuilder
# pour changer l'URL de l'API.
ARG NUXT_PUBLIC_API_BASE=http://localhost:8000
ENV NUXT_PUBLIC_API_BASE=$NUXT_PUBLIC_API_BASE

# ── Build Nuxt (mode SSR Nitro) → frontend/.output ─────────────
RUN pnpm --filter frontend run build

# ═══════════════════════════════════════════════════════════════
# Stage 2 — Runner (image finale légère)
# ═══════════════════════════════════════════════════════════════
FROM node:22-alpine AS runner

WORKDIR /app

# Copier le bundle Nitro depuis le stage builder
COPY --from=builder /app/frontend/.output ./

EXPOSE 3000

# Nitro Node server — lit PORT et NUXT_PUBLIC_* au démarrage
CMD ["node", "server/index.mjs"]

# --- Stage 1: Build (Construction des dépendances) ---
FROM python:3.12-slim AS builder

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Installation des dépendances système nécessaires pour compiler psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Installation des packages Python dans un répertoire temporaire
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Stage 2: Run (Image finale légère) ---
FROM python:3.12-slim

WORKDIR /app

# Installation de libpq5 (nécessaire pour exécuter psycopg2)
RUN apt-get update && apt-get install -y libpq5 && rm -rf /var/lib/apt/lists/*

# Récupération des packages installés au Stage 1
COPY --from=builder /install /usr/local

# Copie du code source du backend vers /app
COPY backend/ .

# --- CONFIGURATION DES CHEMINS ---
# PYTHONPATH=/app/src permet à Python de trouver les modules (core, models, etc.)
# situés dans le dossier /app/src/
ENV PYTHONPATH=/app/src
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Création d'un utilisateur non-root pour la sécurité sur Render
RUN useradd -m mlauser && chown -R mlauser /app
USER mlauser

# --- COMMANDE DE LANCEMENT ---
# 1. alembic upgrade head : Applique les migrations sur la DB Render
# 2. uvicorn main:app : Lance l'API sur le port injecté par Render ($PORT)
CMD sh -c "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port $PORT"
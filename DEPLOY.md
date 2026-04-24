# Déploiement MLA Planning — OVH VPS

IP VPS : `85.184.92.137` · Ubuntu 25.04 · Docker Compose · SSL auto-signé

---

## ÉTAPE 1 — Préparer le VPS (une seule fois, en root)

```bash
ssh root@85.184.92.137
```

```bash
# Mise à jour système
apt update && apt upgrade -y

# Dépendances
apt install -y git openssl ufw curl

# Docker (méthode officielle)
curl -fsSL https://get.docker.com | sh

# Firewall
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
ufw status
```

---

## ÉTAPE 2 — Créer le user deploy (sans sudo)

```bash
useradd -m -s /bin/bash deploy
usermod -aG docker deploy

# Créer la structure
mkdir -p /opt/mla/ssl /opt/mla/nginx
chown -R deploy:deploy /opt/mla
```

---

## ÉTAPE 3 — Clé SSH pour GitHub Actions

```bash
# Toujours en root — génère la clé au nom de deploy
ssh-keygen -t ed25519 -C "github-actions-mla" -f /home/deploy/.ssh/github_actions -N ""

# Autoriser la clé publique pour le user deploy
cat /home/deploy/.ssh/github_actions.pub >> /home/deploy/.ssh/authorized_keys
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys
chown -R deploy:deploy /home/deploy/.ssh

# Afficher la clé PRIVÉE → à copier dans GitHub Secrets (VPS_SSH_KEY)
cat /home/deploy/.ssh/github_actions
```

**Dans GitHub → Settings → Secrets and variables → Actions → New repository secret :**

| Secret | Valeur |
|---|---|
| `VPS_HOST` | `85.184.92.137` |
| `VPS_USER` | `deploy` |
| `VPS_SSH_KEY` | Contenu de la clé privée affichée ci-dessus |

---

## ÉTAPE 4 — Certificat SSL auto-signé

```bash
openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
  -keyout /opt/mla/ssl/mla.key \
  -out    /opt/mla/ssl/mla.crt \
  -subj   "/CN=85.184.92.137" \
  -addext "subjectAltName=IP:85.184.92.137"

chmod 600 /opt/mla/ssl/mla.key
chmod 644 /opt/mla/ssl/mla.crt
```

---

## ÉTAPE 5 — Cloner le repo et configurer

```bash
su - deploy

# Cloner
git clone https://github.com/T-lamo/MLA-Planner.git /opt/mla/repo
cd /opt/mla/repo

# Copier nginx.conf
cp mla-app/nginx/nginx.conf /opt/mla/nginx/nginx.conf
```

---

## ÉTAPE 6 — Créer le fichier .env de production

```bash
cat > /opt/mla/.env << 'EOF'
VPS_IP=85.184.92.137

POSTGRES_USER=mla_user
POSTGRES_PASSWORD=MOT_DE_PASSE_FORT_ICI
POSTGRES_DB=mla_db

DATABASE_URL=postgresql+psycopg2://mla_user:MOT_DE_PASSE_FORT_ICI@db:5432/mla_db
JWT_SECRET_KEY=CLE_JWT_ALEATOIRE_32_CARACTERES_MINIMUM
ENV=production
PORT=8000

SUPERADMIN_USERNAME=superadmin
SUPERADMIN_PASSWORD=MOT_DE_PASSE_SUPERADMIN_ICI

ALLOWED_ORIGINS=https://85.184.92.137
NUXT_PUBLIC_API_BASE=https://85.184.92.137/api

SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
EMAIL_FROM=noreply@mla-planning.com
EMAIL_FROM_NAME=MLA Planner
EOF

chmod 600 /opt/mla/.env
```

> Générer une clé JWT sécurisée :
> ```bash
> openssl rand -hex 32
> ```

---

## ÉTAPE 7 — Créer le script de déploiement

```bash
cat > /opt/mla/deploy.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Déploiement MLA Planning..."

# Pull dernière version
git -C /opt/mla/repo pull origin main

# Synchroniser nginx.conf
cp /opt/mla/repo/mla-app/nginx/nginx.conf /opt/mla/nginx/nginx.conf

# Build + démarrage
cd /opt/mla/repo/mla-app
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  --env-file /opt/mla/.env \
  up --build -d --remove-orphans

echo "✅ Déploiement terminé"
EOF

chmod +x /opt/mla/deploy.sh
```

---

## ÉTAPE 8 — Premier démarrage

```bash
cd /opt/mla/repo/mla-app

# Build + démarrage
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  --env-file /opt/mla/.env \
  up --build -d

# Suivre les logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
```

---

## ÉTAPE 9 — Seed initial (une seule fois)

Une fois le backend démarré et healthy :

```bash
cd /opt/mla/repo/mla-app

docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  --env-file /opt/mla/.env \
  exec backend python scripts/db_admin.py seed
```

---

## Checklist de vérification

```bash
# Health API
curl -k https://85.184.92.137/api/health
# → {"status":"ok"}

# Swagger
# Ouvrir dans le navigateur : https://85.184.92.137/api/docs

# Frontend
# Ouvrir dans le navigateur : https://85.184.92.137

# Firewall
ufw status
# → 22, 80, 443 uniquement

# Logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs --tail=50
```

---

## CI/CD automatique

Après configuration des GitHub Secrets, chaque push sur `main` :
1. GitHub Actions se connecte en SSH au VPS
2. Exécute `/opt/mla/deploy.sh`
3. Vérifie `/api/health` → 200

Surveiller les déploiements : **GitHub → Actions → Deploy to OVH VPS**

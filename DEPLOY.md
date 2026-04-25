# Déploiement MLA Planning — OVH VPS

IP VPS : `57.129.113.31` · Ubuntu 25.04 · Docker Compose · SSL auto-signé

---

## ÉTAPE 1 — Préparer le VPS (une seule fois)

```bash
ssh ubuntu@57.129.113.31
```

```bash
# Mise à jour système
sudo apt update && sudo apt upgrade -y

# Dépendances
sudo apt install -y git openssl ufw curl

# Docker (méthode officielle)
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu
newgrp docker

# Firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
sudo ufw status

# Structure répertoires
sudo mkdir -p /opt/mla/ssl /opt/mla/nginx
sudo chown -R ubuntu:ubuntu /opt/mla
```

---

## ÉTAPE 2 — Clé SSH pour GitHub Actions

```bash
# Générer la clé
ssh-keygen -t ed25519 -C "github-actions-mla" -f ~/.ssh/github_actions -N ""

# Autoriser la clé publique
cat ~/.ssh/github_actions.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Afficher la clé PRIVÉE → copier dans GitHub Secrets (VPS_SSH_KEY)
cat ~/.ssh/github_actions
```

**Dans GitHub → Settings → Secrets and variables → Actions → New repository secret :**

| Secret | Valeur |
|---|---|
| `VPS_HOST` | `57.129.113.31` |
| `VPS_USER` | `ubuntu` |
| `VPS_SSH_KEY` | Contenu complet de la clé privée ci-dessus |

---

## ÉTAPE 3 — Certificat SSL auto-signé

```bash
sudo openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
  -keyout /opt/mla/ssl/mla.key \
  -out    /opt/mla/ssl/mla.crt \
  -subj   "/CN=57.129.113.31" \
  -addext "subjectAltName=IP:57.129.113.31"

sudo chmod 600 /opt/mla/ssl/mla.key
sudo chmod 644 /opt/mla/ssl/mla.crt
sudo chown ubuntu:ubuntu /opt/mla/ssl/mla.key /opt/mla/ssl/mla.crt
```

---

## ÉTAPE 4 — Cloner le repo

```bash
git clone https://github.com/T-lamo/MLA-Planner.git /opt/mla/repo
cp /opt/mla/repo/nginx/nginx.conf /opt/mla/nginx/nginx.conf
```

---

## ÉTAPE 5 — Créer le fichier .env de production

```bash
# Générer une clé JWT sécurisée
openssl rand -hex 32

nano /opt/mla/.env
```

Contenu du `.env` (remplacer les CHANGE_ME) :

```
VPS_IP=57.129.113.31

POSTGRES_USER=mla_user
POSTGRES_PASSWORD=CHANGE_ME_strong_password
POSTGRES_DB=mla_db

DATABASE_URL=postgresql+psycopg2://mla_user:CHANGE_ME_strong_password@db:5432/mla_db
JWT_SECRET_KEY=CHANGE_ME_32_chars_minimum_random_key
ENV=production
PORT=8000

SUPERADMIN_USERNAME=superadmin
SUPERADMIN_PASSWORD=CHANGE_ME_superadmin_password

ALLOWED_ORIGINS=https://57.129.113.31
NUXT_PUBLIC_API_BASE=https://57.129.113.31/api

SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
EMAIL_FROM=noreply@mla-planning.com
EMAIL_FROM_NAME=MLA Planner
```

```bash
chmod 600 /opt/mla/.env
```

---

## ÉTAPE 6 — Créer le script de déploiement

```bash
tee /opt/mla/deploy.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Déploiement MLA Planning..."

# Correction permissions
sudo chown -R ubuntu:ubuntu /opt/mla/repo
sudo chown -R ubuntu:ubuntu /opt/mla/nginx

# Pull dernière version
git -C /opt/mla/repo pull origin main

# Synchroniser nginx.conf
cp /opt/mla/repo/nginx/nginx.conf /opt/mla/nginx/nginx.conf

# Build + démarrage
cd /opt/mla/repo/
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  --env-file /opt/mla/.env \
  up --build -d --remove-orphans

echo "✅ Déploiement terminé"
EOF

chmod +x /opt/mla/deploy.sh
```

Autoriser les chown sans mot de passe :

```bash
echo "ubuntu ALL=(ALL) NOPASSWD: /bin/chown -R ubuntu:ubuntu /opt/mla*" \
  | sudo tee /etc/sudoers.d/mla-deploy
```

---

## ÉTAPE 7 — Premier démarrage

```bash
cd /opt/mla/repo/

docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  --env-file /opt/mla/.env \
  up --build -d

# Suivre les logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
```

---

## ÉTAPE 8 — Seed initial (une seule fois)

```bash
cd /opt/mla/repo/

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
curl -k https://57.129.113.31/api/health
# → {"status":"ok"}

# Swagger : https://57.129.113.31/api/docs
# Frontend : https://57.129.113.31

# Firewall
sudo ufw status

# Logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs --tail=50
```

---

## CI/CD automatique

Après configuration des GitHub Secrets, chaque push sur `main` :
1. GitHub Actions se connecte en SSH (`ubuntu@57.129.113.31`)
2. Exécute `/opt/mla/deploy.sh`
3. Vérifie `/api/health` → 200

Surveiller : **GitHub → Actions → Deploy to OVH VPS**

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
sudo mkdir -p /opt/mla/nginx /var/www/certbot
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

## ÉTAPE 3 — Certificat SSL Let's Encrypt (Certbot)

```bash
# Installer certbot
sudo apt install -y certbot

# Créer le répertoire webroot pour le challenge ACME
sudo mkdir -p /var/www/certbot

# Démarrer nginx en HTTP seulement (commentez le bloc 443 ou utilisez une conf temporaire)
# OU démarrez directement les containers HTTP — nginx gérera /.well-known/acme-challenge/

# Obtenir le certificat (DNS doit déjà pointer vers ce VPS)
sudo certbot certonly --webroot \
  -w /var/www/certbot \
  -d plannerchurch.com \
  -d www.plannerchurch.com \
  --email amosdorceus2023@gmail.com \
  --agree-tos \
  --no-eff-email

# Vérification
sudo ls /etc/letsencrypt/live/plannerchurch.com/
# → fullchain.pem  privkey.pem  chain.pem  cert.pem

# Renouvellement automatique (cron)
echo "0 3 * * * root certbot renew --quiet --deploy-hook 'docker exec repo-nginx-1 nginx -s reload'" \
  | sudo tee /etc/cron.d/certbot-renew
```

> **Note** : Si nginx n'est pas encore démarré, utilisez le mode standalone :
> `sudo certbot certonly --standalone -d plannerchurch.com -d www.plannerchurch.com --email amosdorceus2023@gmail.com --agree-tos --no-eff-email`

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
DOMAIN=plannerchurch.com

POSTGRES_USER=mla_user
POSTGRES_PASSWORD=CHANGE_ME_strong_password
POSTGRES_DB=mla_db

DATABASE_URL=postgresql+psycopg2://mla_user:CHANGE_ME_strong_password@db:5432/mla_db
JWT_SECRET_KEY=CHANGE_ME_32_chars_minimum_random_key
ENV=production
PORT=8000

SUPERADMIN_USERNAME=superadmin
SUPERADMIN_PASSWORD=CHANGE_ME_superadmin_password

ALLOWED_ORIGINS=https://plannerchurch.com,https://www.plannerchurch.com
NUXT_PUBLIC_API_BASE=https://plannerchurch.com/api

SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
EMAIL_FROM=noreply@plannerchurch.com
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
curl https://plannerchurch.com/api/health
# → {"status":"ok"}

# Swagger : https://plannerchurch.com/api/docs
# Frontend : https://plannerchurch.com

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

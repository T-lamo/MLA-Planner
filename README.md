# 🚀 MLA / ICC — Service Planning Application

![CI](https://github.com/T-lamo/MLA-Planner/actions/workflows/ci.yml/badge.svg)
![Coverage](https://codecov.io/gh/T-lamo/MLA-Planner/branch/main/graph/badge.svg)

> Application moderne de planification de services pour le projet **MLA / ICC**, conçue pour être **rapide, sécurisée et scalable**.

---

## 📌 À propos
Le projet **MLA / ICC Planner** a pour objectif de fournir une **solution web complète pour la gestion et la planification de services**.  
Il centralise les informations, automatise les processus et assure la cohérence grâce à une architecture robuste et modulable.

**Objectifs principaux :**
- Gestion des membres, équipes et rôles
- Planification et suivi des activités
- Respect des bonnes pratiques de développement et sécurité
- Tests automatisés et CI/CD pour garantir la qualité du code

---

## 🧱 Stack Technique

### Backend
- ⚡ **Framework** : FastAPI (asynchrone, rapide)
- 🗄️ **Base de données** : PostgreSQL  
- 🧩 **ORM** : SQLModel + SQLAlchemy  
- 🔐 **Authentification & sécurité** : JWT, Python-Jose, Passlib  
- 📦 **Migrations** : Alembic  
- 🐳 **Déploiement** : Docker

### DevOps / CI/CD
- 🔄 **CI/CD** : GitHub Actions  
- ✅ **Tests & coverage** : pytest + pytest-cov + Codecov  
- 🔎 **Type checking** : Mypy  
- 🖌️ **Style & linting** : Black, Isort, Pylint  
- 🪝 **Pre-commit hooks** : Black, Isort, Mypy, Pylint  
- 📜 **Logging** : Loguru  

### Frontend
- ⚡ **Framework** : Vue.js (planifié)

---

## ⚙️ Commandes Utiles

### Linting et formatage
```bash
# Formatter le code
black src/ tests/

# Organiser les imports
isort src/ tests/

# Linter le code
pylint src/ 

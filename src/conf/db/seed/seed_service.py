import logging
from datetime import datetime, timedelta
from typing import Optional, Type, TypeVar

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, SQLModel, select

from core.auth.security import get_password_hash
from models import (
    Activite,
    Affectation,
    AffectationRole,
    Campus,
    CategorieRole,
    Equipe,
    Equipe_Membre,
    Indisponibilite,
    Membre,
    Membre_Role,
    Ministere,
    OrganisationICC,
    Pays,
    Permission,
    PlanningService,
    Pole,
    Responsabilite,
    Role,
    RoleCompetence,
    RolePermission,
    StatutPlanning,
    TypeResponsabilite,
    Utilisateur,
)

from .data import (
    ACTIVITES_DATA,
    CATEGORIES_ROLES,
    EQUIPE_MEMBRES_DATA,
    EQUIPES_DATA,
    MEMBRES_INFOS,
    MINISTERES_DATA,
    PERMISSIONS,
    POLES_DATA,
    RESPONSABILITES_DATA,
    ROLES,
    ROLES_COMPETENCES,
    SEED_CAMPUS,
    SEED_ORGANISATIONS,
    SEED_PAYS,
    STATUTS_PLANNING,
    TYPES_RESPONSABILITE,
    MembreInfo,
)

T = TypeVar("T", bound=SQLModel)


class SeedService:
    def __init__(self, db: Session, logger: logging.Logger | None = None):
        self.db = db
        self.logger = logger or logging.getLogger("seed_service")

    def run(self):
        self.logger.info("🚀 Lancement du Seed Refactoré (Nouveau Schéma)...")
        try:
            with self.db.begin():
                # 1. GÉOGRAPHIE (IDs: str)
                org_map = self._seed_organisations()
                pays_map = self._seed_pays(org_map)
                campus_map = self._seed_campus(pays_map)
                campus_paris = campus_map["Campus Paris"]

                # 2. RBAC & SÉCURITÉ
                role_map = self._seed_roles(ROLES)
                perm_map = self._seed_permissions(PERMISSIONS)
                self._seed_role_permissions(role_map, PERMISSIONS, perm_map)
                user_list = self._seed_users_for_roles(role_map)

                # 3. RÉFÉRENTIELS MÉTIER (Nouveau Schéma)
                self._seed_categories_et_roles()
                self._seed_referentiels_fixes()

                min_map = self._seed_ministeres(campus_paris.id)
                pole_map = self._seed_poles(min_map)
                act_map = self._seed_activites(campus_paris.id)

                # 4. RH & POLYVALENCE (IDs: uuid.UUID)
                # Remplace l'ancien _seed_rh_complet
                self._seed_membres_et_competences(
                    user_list, campus_paris.id, min_map, pole_map
                )

                # 5. OPÉRATIONNEL
                eq_map = self._seed_equipes(min_map)
                self._seed_equipe_membres(eq_map, user_list)
                self._seed_responsabilites(user_list, min_map, pole_map)
                self._seed_planning_complet(act_map, user_list)

            self.logger.info("✅ Seed terminé avec succès (Polyvalence activée) !")
        except SQLAlchemyError as e:
            self.logger.error(f"❌ Erreur critique: {str(e)}")
            raise

    # --- MÉTHODES DE BASE ---

    def _get_or_create(
        self, model: Type[T], defaults: Optional[dict] = None, **filters
    ) -> tuple[T, bool]:
        stmt = select(model).filter_by(**filters)
        instance = self.db.exec(stmt).first()
        if instance:
            return instance, False
        params = {**filters, **(defaults or {})}
        obj = model(**params)
        self.db.add(obj)
        self.db.flush()
        return obj, True

    # --- GEOGRAPHIE ---

    def _seed_organisations(self):
        return {
            d["nom"]: self._get_or_create(
                OrganisationICC,
                nom=d["nom"],
                defaults={"date_creation": d["date_creation"]},
            )[0]
            for d in SEED_ORGANISATIONS
        }

    def _seed_pays(self, org_map):
        return {
            d["nom"]: self._get_or_create(
                Pays,
                nom=d["nom"],
                defaults={
                    "code": d["code"],  # Correction: passage du code obligatoire
                    "organisation_id": org_map[d["org_nom"]].id,
                },
            )[0]
            for d in SEED_PAYS
        }

    def _seed_campus(self, pays_map):
        return {
            d["nom"]: self._get_or_create(
                Campus,
                nom=d["nom"],
                defaults={
                    "pays_id": pays_map[d["pays_nom"]].id,
                    "ville": d["ville"],
                    "timezone": d["timezone"],
                },
            )[0]
            for d in SEED_CAMPUS
        }

    # --- NOUVEAU SCHÉMA COMPÉTENCES ---

    def _seed_categories_et_roles(self):
        self.logger.info("🏷️ Création des catégories et rôles de compétences...")
        for cat in CATEGORIES_ROLES:
            self._get_or_create(
                CategorieRole, code=cat["code"], defaults={"libelle": cat["libelle"]}
            )
        for rc in ROLES_COMPETENCES:
            self._get_or_create(
                RoleCompetence,
                code=rc["code"],
                defaults={"libelle": rc["libelle"], "categorie_code": rc["cat"]},
            )

    def _seed_referentiels_fixes(self):
        for stat in STATUTS_PLANNING:
            self._get_or_create(StatutPlanning, code=stat)
        for resp in TYPES_RESPONSABILITE:
            self._get_or_create(TypeResponsabilite, code=resp)

    # --- RH & POLYVALENCE ---

    def _seed_membres_et_competences(self, users, campus_id: str, min_map, pole_map):
        """
        Crée les membres, les lie aux utilisateurs et définit leurs compétences.
        Respecte la polyvalence (un membre -> plusieurs rôles).
        """
        self.logger.info("👥 Création des membres et de la polyvalence...")

        for i, user in enumerate(users):
            # Récupération sécurisée des infos (Mypy friendly)
            info: MembreInfo = MEMBRES_INFOS[i % len(MEMBRES_INFOS)]

            # 1. Création du Membre (ID généré en uuid.UUID par défaut dans le modèle)
            membre, _ = self._get_or_create(
                Membre,
                email=info["email"],
                defaults={
                    "nom": info["nom"],
                    "prenom": info["prenom"],
                    "campus_id": campus_id,
                    "ministere_id": min_map["Louange et Adoration"].id,
                    "pole_id": (
                        pole_map["Chorale"].id
                        if i % 2 == 0
                        else pole_map["Musiciens"].id
                    ),
                    "actif": True,
                    "date_inscription": datetime.now(),
                },
            )

            # 2. Mise à jour de l'Utilisateur (Liaison 1-1)
            user.membre_id = membre.id
            self.db.add(user)
            self.db.flush()

            # 3. Assignation des Rôles de Compétences (Polyvalence)
            roles_a_assigner = info.get("roles", [])
            for index_r, role_code in enumerate(roles_a_assigner):
                # Le premier rôle de la liste est considéré comme principal
                is_principal = index_r == 0

                self._get_or_create(
                    Membre_Role,
                    membre_id=membre.id,
                    role_code=role_code,
                    defaults={"niveau": "CONFIRME", "is_principal": is_principal},
                )
                self.logger.debug(f"   - Rôle {role_code} assigné à {info['nom']}")

            # 4. Création d'une indisponibilité exemple pour le premier membre
            if i == 0:
                self._get_or_create(
                    Indisponibilite,
                    membre_id=membre.id,
                    defaults={
                        "date_debut": datetime.now() + timedelta(days=2),
                        "date_fin": datetime.now() + timedelta(days=4),
                        "motif": "Déplacement professionnel",
                    },
                )

    # --- PLANNING ---

    def _seed_planning_complet(self, act_map, users):
        self.logger.info("📅 Génération du planning et des affectations...")
        if not act_map.get("Culte"):
            return

        plan, _ = self._get_or_create(
            PlanningService,
            activite_id=act_map["Culte"].id,
            defaults={"statut_code": "PUBLIE"},
        )

        # Premier membre (index 0)
        if users[0].membre_id:
            self._get_or_create(
                Affectation,
                planning_id=plan.id,
                membre_id=users[0].membre_id,
                role_code="TENOR",
                defaults={"presence_confirmee": True},
            )

        # Deuxième membre (on utilise l'index 1 au lieu de 3 pour être sûr qu'il existe)
        if len(users) > 1 and users[1].membre_id:
            self._get_or_create(
                Affectation,
                planning_id=plan.id,
                membre_id=users[1].membre_id,
                role_code="PIANO",  # Ou un autre code valide
                defaults={"presence_confirmee": False},
            )

    # --- RESTE DU SEED (Ministeres, Poles, Equipes, etc.) ---

    def _seed_ministeres(self, campus_id):
        self.logger.info("🏛️ Création des ministères...")
        return {
            m["nom"]: self._get_or_create(
                Ministere,
                nom=m["nom"],
                defaults={
                    "campus_id": campus_id,
                    "date_creation": m[
                        "date_creation"
                    ],  # Récupère la date de MINISTERES_DATA
                    "actif": m.get("actif", True),  # Récupère le statut actif
                },
            )[0]
            for m in MINISTERES_DATA
        }

    def _seed_poles(self, min_map):
        p_map = {}
        for m_nom, poles in POLES_DATA.items():
            for p in poles:
                pole, _ = self._get_or_create(
                    Pole, nom=p["nom"], ministere_id=min_map[m_nom].id
                )
                p_map[p["nom"]] = pole
        return p_map

    def _seed_activites(self, cid):
        self.logger.info("🎭 Création des activités...")
        return {
            a["type"]: self._get_or_create(
                Activite,
                # Correction: On utilise 'type' au lieu de 'nom' pour le filtre
                # (Vérifie si ton modèle utilise 'type' ou 'libelle')
                type=a["type"],
                defaults={
                    "campus_id": cid,
                    "lieu": a.get("lieu", "Lieu par défaut"),
                    "date_creation": datetime.now(),
                    "date_debut": datetime.now(),
                    "date_fin": datetime.now() + timedelta(hours=2),
                },
            )[0]
            for a in ACTIVITES_DATA
        }

    def _seed_equipes(self, mm):
        return {
            eq_nom: self._get_or_create(Equipe, nom=eq_nom, ministere_id=mm[mn].id)[0]
            for mn, eqs in EQUIPES_DATA.items()
            for eq_nom in eqs
        }

    def _seed_equipe_membres(self, eq_map, user_list):
        for data in EQUIPE_MEMBRES_DATA:
            equipe = eq_map.get(data["equipe_nom"])
            user = user_list[data["user_index"]]
            if equipe and user.membre_id:
                self._get_or_create(
                    Equipe_Membre, equipe_id=equipe.id, membre_id=user.membre_id
                )

    def _seed_responsabilites(self, user_list, min_map, pole_map):
        for res in RESPONSABILITES_DATA:
            user = user_list[res["user_index"]]
            if user.membre_id:
                self._get_or_create(
                    Responsabilite,
                    membre_id=user.membre_id,
                    type_code=res["type"],
                    defaults={
                        "ministere_id": min_map[res["ministere"]].id,
                        "pole_id": pole_map[res["pole"]].id,
                    },
                )

    def _seed_roles(self, lib):
        self.logger.info("🔑 Création des rôles RBAC...")
        # On utilise 'libelle' car c'est le nom défini dans RoleBase
        return {r: self._get_or_create(Role, libelle=r)[0] for r in lib}

    def _seed_permissions(self, d):
        perms = {}
        for codes in d.values():
            for c in codes:
                obj, _ = self._get_or_create(Permission, code=c)
                perms[c] = obj
        return perms

    def _seed_role_permissions(self, rm, pd, pm):
        for rn, codes in pd.items():
            for c in codes:
                self._get_or_create(
                    RolePermission, role_id=rm[rn].id, permission_id=pm[c].id
                )

    def _seed_users_for_roles(self, rm):
        users = []
        for rn, role in rm.items():
            u, _ = self._get_or_create(
                Utilisateur,
                username=f"user_{rn.lower()}",
                defaults={"password": get_password_hash("Admin123!"), "actif": True},
            )
            self._get_or_create(AffectationRole, utilisateur_id=u.id, role_id=role.id)
            users.append(u)
        return users

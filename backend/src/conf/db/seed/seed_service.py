import logging
from datetime import datetime, timedelta
from typing import Optional, Type, TypeVar

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, SQLModel, select

from core.auth.security import get_password_hash
from mla_enum import RoleName
from models import Slot  # Nouveau
from models import StatutAffectation  # Nouveau
from models import (
    Activite,
    Affectation,
    AffectationRole,
    Campus,
    CampusMinistereLink,
    CategorieRole,
    Equipe,
    EquipeMembre,
    Membre,
    MembreCampusLink,
    MembreMinistereLink,
    MembrePoleLink,
    MembreRole,
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
    SUPERADMIN_PASSWORD,
    SUPERADMIN_USERNAME,
    TYPES_RESPONSABILITE,
    MembreInfo,
)

T = TypeVar("T", bound=SQLModel)


class SeedService:
    def __init__(self, db: Session, logger: logging.Logger | None = None):
        self.db = db
        self.logger = logger or logging.getLogger("seed_service")

    def run(self):
        self.logger.info(
            "🚀 Lancement du Seed Refactoré (Architecture Slots & Compétences)..."
        )
        try:
            with self.db.begin():
                # 1. GÉOGRAPHIE
                org_map = self._seed_organisations()
                pays_map = self._seed_pays(org_map)
                campus_map = self._seed_campus(pays_map)
                campus_paris = campus_map["Campus Paris"]

                # 2. RBAC & SÉCURITÉ
                role_map = self._seed_roles(ROLES)
                perm_map = self._seed_permissions(PERMISSIONS)
                self._seed_role_permissions(role_map, PERMISSIONS, perm_map)
                user_list = self._seed_users_for_roles(role_map)

                # 3. RÉFÉRENTIELS MÉTIER
                self._seed_categories_et_roles()
                self._seed_referentiels_fixes()

                min_map = self._seed_ministeres(default_campus_id=campus_paris.id)
                pole_map = self._seed_poles(min_map)

                # Correction Activite : nécessite un ministère organisateur
                default_min = min_map["Louange et Adoration"]
                act_map = self._seed_activites(campus_paris.id, default_min.id)

                # 4. RH & POLYVALENCE
                self._seed_membres_et_competences(
                    user_list, campus_map, min_map, pole_map
                )

                # 5. OPÉRATIONNEL & PLANNING (Cœur de la modification)
                eq_map = self._seed_equipes(min_map)
                self._seed_equipe_membres(eq_map, user_list)
                self._seed_responsabilites(user_list, min_map, pole_map)
                self._seed_planning_complet(act_map, user_list)

            self.logger.info("✅ Seed terminé avec succès !")
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

    # --- RÉFÉRENTIELS ---

    def _seed_referentiels_fixes(self):
        for stat in STATUTS_PLANNING:
            self._get_or_create(StatutPlanning, code=stat)
        for resp in TYPES_RESPONSABILITE:
            self._get_or_create(TypeResponsabilite, code=resp)
        # Nouveaux statuts d'affectation
        for s_aff in ["PROPOSE", "CONFIRME", "REFUSE", "PRESENT"]:
            self._get_or_create(StatutAffectation, code=s_aff)

    # --- GEOGRAPHIE & STRUCTURE ---

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
                    "code": d["code"],
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

    def _seed_ministeres(self, default_campus_id: str) -> dict[str, Ministere]:
        """
        Peuple les ministères et crée les liens Many-to-Many avec les campus.
        """
        min_map: dict[str, Ministere] = {}

        for m in MINISTERES_DATA:
            m_nom = str(m["nom"])  # Conversion explicite pour garantir le type str

            # 1. Création ou récupération du Ministère
            ministere, _ = self._get_or_create(
                Ministere,
                nom=m_nom,
                defaults={
                    "date_creation": m["date_creation"],
                    "actif": m.get("actif", True),
                },
            )

            # 2. Liaison Many-to-Many
            self._get_or_create(
                CampusMinistereLink,
                campus_id=default_campus_id,
                ministere_id=ministere.id,
            )

            min_map[m_nom] = ministere

        return min_map

    def _seed_poles(self, min_map):
        p_map = {}
        for m_nom, poles in POLES_DATA.items():
            for p in poles:
                pole, _ = self._get_or_create(
                    Pole, nom=p["nom"], ministere_id=min_map[m_nom].id
                )
                p_map[p["nom"]] = pole
        return p_map

    # --- RH & COMPÉTENCES ---

    def _seed_categories_et_roles(self):
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

    def _seed_membres_et_competences(
        self, users: list, campus_map: dict, min_map: dict, pole_map: dict
    ) -> None:
        """Gère la création des membres et délègue la création des liens N:N."""
        self.logger.info("👥 Peuplement des membres et des tables de liaison N:N...")

        for i, user in enumerate(users):
            info: MembreInfo = MEMBRES_INFOS[i % len(MEMBRES_INFOS)]

            # 1. Création du Membre
            membre, _ = self._get_or_create(
                Membre,
                email=info["email"],
                defaults={
                    "nom": info["nom"],
                    "prenom": info["prenom"],
                    "actif": True,
                },
            )

            # Liaison avec l'utilisateur technique
            user.membre_id = membre.id
            self.db.add(user)

            # Dans _seed_membres_et_competences :
            self._link_member_to_entities(
                membre.id,
                info,
                c_map=campus_map,  # Argument nommé
                m_map=min_map,  # Argument nommé
                p_map=pole_map,  # Argument nommé
            )
            self._assign_member_roles(membre.id, info.get("roles") or [])

            # Définit le campus principal (idempotent)
            campus_names = info.get("campus_names") or []
            if campus_names and campus_names[0] in campus_map:
                principal_id = campus_map[campus_names[0]].id
                if membre.campus_principal_id != principal_id:
                    membre.campus_principal_id = principal_id
                    self.db.add(membre)
                    self.db.flush()

    def _link_member_to_entities(
        self,
        m_id: str,
        info: MembreInfo,
        *,  # <--- Tout ce qui suit doit être nommé à l'appel
        c_map: dict,
        m_map: dict,
        p_map: dict,
    ) -> None:
        """Gère les liaisons Many-to-Many (Campus, Ministères, Pôles)."""

        # Campus
        for c_name in info.get("campus_names") or ["Campus Paris"]:
            if c_name in c_map:
                self._get_or_create(
                    MembreCampusLink, membre_id=m_id, campus_id=c_map[c_name].id
                )

        # Ministères
        for m_name in info.get("ministere_names") or []:
            if m_name in m_map:
                self._get_or_create(
                    MembreMinistereLink, membre_id=m_id, ministere_id=m_map[m_name].id
                )

        # Pôles
        for p_name in info.get("pole_names") or []:
            if p_name in p_map:
                self._get_or_create(
                    MembrePoleLink, membre_id=m_id, pole_id=p_map[p_name].id
                )

    def _assign_member_roles(self, m_id: str, roles: list[str]) -> None:
        """Assignation des rôles techniques (Polyvalence)."""
        for idx, role_code in enumerate(roles):
            self._get_or_create(
                MembreRole,
                membre_id=m_id,
                role_code=role_code,
                defaults={"niveau": "DEBUTANT", "is_principal": (idx == 0)},
            )

    # --- PLANNING (LOGIQUE SLOTS) ---

    def _seed_planning_complet(self, act_map, users):
        self.logger.info("📅 Génération Slots et Affectations...")
        culte = act_map.get("Culte")
        if not culte:
            return

        # 1. Création du Planning
        plan, _ = self._get_or_create(
            PlanningService, activite_id=culte.id, defaults={"statut_code": "PUBLIE"}
        )

        # 2. Création d'un Slot (Créneau horaire)
        slot_matin, _ = self._get_or_create(
            Slot,
            planning_id=plan.id,
            nom_creneau="Service Dominical Matin",
            defaults={"date_debut": culte.date_debut, "date_fin": culte.date_fin},
        )

        # 3. Affectations sur le Slot (Vérification des rôles du membre)
        # On affecte Amos (Index 0) comme TENOR sur le slot
        if users[0].membre_id:
            self._get_or_create(
                Affectation,
                slot_id=slot_matin.id,
                membre_id=users[0].membre_id,
                role_code="TENOR",  # Amos a bien ce rôle dans MEMBRES_INFOS
                defaults={
                    "statut_affectation_code": "CONFIRME",
                    "presence_confirmee": True,
                },
            )

        # On affecte Marie (Index 3 si existe) ou Index 1 comme PIANO
        target_idx = 3 if len(users) > 3 else 1
        if users[target_idx].membre_id:
            # On récupère le premier rôle dispo pour ce membre
            #  pour éviter l'erreur de FK
            role_to_use = MEMBRES_INFOS[target_idx % len(MEMBRES_INFOS)]["roles"][0]
            self._get_or_create(
                Affectation,
                slot_id=slot_matin.id,
                membre_id=users[target_idx].membre_id,
                role_code=role_to_use,
                defaults={
                    "statut_affectation_code": "PROPOSE",
                    "presence_confirmee": False,
                },
            )

    # --- AUTRES MÉTHODES ---

    def _seed_activites(self, cid, min_org_id):
        return {
            a["type"]: self._get_or_create(
                Activite,
                type=a["type"],
                defaults={
                    "campus_id": cid,
                    "lieu": a.get("lieu", "Lieu par défaut"),
                    "date_creation": datetime.now(),
                    "date_debut": datetime.now(),
                    "date_fin": datetime.now() + timedelta(hours=2),
                    "ministere_organisateur_id": min_org_id,
                },
            )[0]
            for a in ACTIVITES_DATA
        }

    def _seed_roles(self, lib):
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
        """
        Crée les utilisateurs techniques pour chaque rôle.
        Le SUPER_ADMIN a un compte fixe sans lien membre.
        Les autres rôles ont un compte avec username basé sur la clé d'enum.
        Retourne uniquement les utilisateurs non-superadmin (pour le seed membres).
        """
        users = []
        for rn, role in rm.items():
            if rn == RoleName.SUPER_ADMIN:
                # Compte superadmin fixe — pas de lien membre
                u, _ = self._get_or_create(
                    Utilisateur,
                    username=SUPERADMIN_USERNAME,
                    defaults={
                        "password": get_password_hash(SUPERADMIN_PASSWORD),
                        "actif": True,
                    },
                )
                self._get_or_create(
                    AffectationRole, utilisateur_id=u.id, role_id=role.id
                )
                # Ne pas inclure dans users (pas de membre associé)
            else:
                # username basé sur la clé d'enum (ex: "admin", "responsable_mla")
                username = f"user_{rn.name.lower()}"
                u, _ = self._get_or_create(
                    Utilisateur,
                    username=username,
                    defaults={
                        "password": get_password_hash("Admin123!"),
                        "actif": True,
                    },
                )
                self._get_or_create(
                    AffectationRole, utilisateur_id=u.id, role_id=role.id
                )
                users.append(u)
        return users

    def _seed_equipes(self, mm: dict[str, Ministere]) -> dict[str, Equipe]:
        eq_map: dict[str, Equipe] = {}

        # mn: Ministere Name, eqs: List of Equipe Names
        for mn, eqs in EQUIPES_DATA.items():
            # On s'assure que mn est traité comme une str pour l'indexation
            ministere = mm.get(str(mn))

            if not ministere:
                self.logger.warning(
                    f"⚠️ Ministère '{mn}' non trouvé pour la création d'équipes."
                )
                continue

            for eq_nom in eqs:
                equipe, _ = self._get_or_create(
                    Equipe, nom=eq_nom, ministere_id=ministere.id
                )
                eq_map[eq_nom] = equipe
        return eq_map

    def _seed_equipe_membres(self, eq_map, user_list):
        for data in EQUIPE_MEMBRES_DATA:
            equipe = eq_map.get(data["equipe_nom"])
            user = user_list[data["user_index"]]
            if equipe and user.membre_id:
                self._get_or_create(
                    EquipeMembre, equipe_id=equipe.id, membre_id=user.membre_id
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

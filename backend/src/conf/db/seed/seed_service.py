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
    USER_PASSWORD,
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

                min_map = self._seed_ministeres(campus_map=campus_map)
                pole_map = self._seed_poles(min_map)

                # today partagé entre activités et plannings pour des dates cohérentes
                today = datetime.now().replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                act_map = self._seed_activites(campus_paris.id, min_map, today)

                # 4. RH & POLYVALENCE
                self._seed_membres_et_competences(
                    user_list, campus_map, min_map, pole_map
                )

                # 5. OPÉRATIONNEL & PLANNING (Cœur de la modification)
                eq_map = self._seed_equipes(min_map)
                self._seed_equipe_membres(eq_map, user_list)
                self._seed_responsabilites(user_list, min_map, pole_map)
                self._seed_planning_complet(act_map, user_list, today)

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

    def _seed_ministeres(self, campus_map: dict) -> dict[str, Ministere]:
        """
        Peuple les ministères et les lie à TOUS les campus (fix 404 multi-campus).
        """
        min_map: dict[str, Ministere] = {}

        for m in MINISTERES_DATA:
            m_nom = str(m["nom"])

            ministere, _ = self._get_or_create(
                Ministere,
                nom=m_nom,
                defaults={
                    "date_creation": m["date_creation"],
                    "actif": m.get("actif", True),
                },
            )

            # Lier le ministère à TOUS les campus — évite les 404 lors d'un
            # changement de campus
            for campus in campus_map.values():
                self._get_or_create(
                    CampusMinistereLink,
                    campus_id=campus.id,
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
            #  (idempotent — ne pas écraser un lien existant)
            if not user.membre_id:
                user.membre_id = membre.id
                self.db.add(user)
                self.db.flush()

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

    def _seed_affectation(
        self,
        slot_id: str,
        membre_id: str,
        role_code: str,
        *,
        statut: str = "CONFIRME",
        present: bool = True,
    ) -> None:
        if not membre_id:
            return
        self._get_or_create(
            Affectation,
            slot_id=slot_id,
            membre_id=membre_id,
            role_code=role_code,
            defaults={"statut_affectation_code": statut, "presence_confirmee": present},
        )

    def _seed_p1_culte_dominical(self, act_map, u0, u1, d_dim1: datetime) -> None:
        """P1 — Culte Dominical — PUBLIE — J+7. Couvre A3, B1, B2, C1, C2."""
        act = act_map.get("Culte Dominical")
        if not act:
            return
        plan, _ = self._get_or_create(
            PlanningService, activite_id=act.id, defaults={"statut_code": "PUBLIE"}
        )
        # s1c — 7h-9h, nb_req=2, Amos REFUSE → 50% (B1)
        s1c, _ = self._get_or_create(
            Slot,
            planning_id=plan.id,
            nom_creneau="Chorale Répétition Pré-Culte",
            defaults={
                "date_debut": d_dim1.replace(hour=7),
                "date_fin": d_dim1.replace(hour=9),
                "nb_personnes_requis": 2,
            },
        )
        self._seed_affectation(
            s1c.id, u0.membre_id, "TENOR", statut="REFUSE", present=False
        )
        # s1a — 9h-12h, nb_req=2, 2 affectations → 100% (C1, B2)
        s1a, _ = self._get_or_create(
            Slot,
            planning_id=plan.id,
            nom_creneau="Équipe Louange Matin",
            defaults={
                "date_debut": d_dim1.replace(hour=9),
                "date_fin": d_dim1.replace(hour=12),
                "nb_personnes_requis": 2,
            },
        )
        self._seed_affectation(s1a.id, u0.membre_id, "TENOR")
        self._seed_affectation(s1a.id, u1.membre_id, "SON")
        # s1b — 18h-21h, nb_req=2, 1 affectation → 50% (C1, C2)
        s1b, _ = self._get_or_create(
            Slot,
            planning_id=plan.id,
            nom_creneau="Équipe Louange Soir",
            defaults={
                "date_debut": d_dim1.replace(hour=18),
                "date_fin": d_dim1.replace(hour=21),
                "nb_personnes_requis": 2,
            },
        )
        self._seed_affectation(
            s1b.id, u0.membre_id, "PIANO", statut="PROPOSE", present=False
        )

    def _seed_p2_repetition_chorale(self, act_map, u0, u1, d_mer: datetime) -> None:
        """P2 — Répétition Chorale — BROUILLON — J+10. Couvre A3
        (is_ready_for_publish)."""
        act = act_map.get("Repetition Chorale")
        if not act:
            return
        plan, _ = self._get_or_create(
            PlanningService, activite_id=act.id, defaults={"statut_code": "BROUILLON"}
        )
        s2, _ = self._get_or_create(
            Slot,
            planning_id=plan.id,
            nom_creneau="Répétition Générale",
            defaults={
                "date_debut": d_mer.replace(hour=19),
                "date_fin": d_mer.replace(hour=21, minute=30),
                "nb_personnes_requis": 2,
            },
        )
        self._seed_affectation(
            s2.id, u0.membre_id, "TENOR", statut="PROPOSE", present=False
        )
        self._seed_affectation(
            s2.id, u1.membre_id, "SON", statut="PROPOSE", present=False
        )

    def _seed_p3_second_culte(self, act_map, u0, u1, d_dim3: datetime) -> None:
        """P3 — Second Culte Louange — TERMINE — J+28. Couvre A3 (immutabilité)."""
        act = act_map.get("Second Culte Louange")
        if not act:
            return
        plan, _ = self._get_or_create(
            PlanningService, activite_id=act.id, defaults={"statut_code": "TERMINE"}
        )
        s3, _ = self._get_or_create(
            Slot,
            planning_id=plan.id,
            nom_creneau="Culte de Clôture",
            defaults={
                "date_debut": d_dim3.replace(hour=10),
                "date_fin": d_dim3.replace(hour=13),
                "nb_personnes_requis": 2,
            },
        )
        self._seed_affectation(s3.id, u0.membre_id, "TENOR")
        self._seed_affectation(s3.id, u1.membre_id, "SON")

    def _seed_p4_technique_dim(self, act_map, u1, d_dim1: datetime) -> None:
        """P4 — Service Technique Dimanche — PUBLIE — J+7. Couvre A3, B2."""
        act = act_map.get("Service Technique Dim")
        if not act:
            return
        plan, _ = self._get_or_create(
            PlanningService, activite_id=act.id, defaults={"statut_code": "PUBLIE"}
        )
        s4a, _ = self._get_or_create(
            Slot,
            planning_id=plan.id,
            nom_creneau="Régie Son — Culte Matin",
            defaults={
                "date_debut": d_dim1.replace(hour=8),
                "date_fin": d_dim1.replace(hour=13),
                "nb_personnes_requis": 2,
            },
        )
        s4b, _ = self._get_or_create(
            Slot,
            planning_id=plan.id,
            nom_creneau="Régie Son — Culte Soir",
            defaults={
                "date_debut": d_dim1.replace(hour=17),
                "date_fin": d_dim1.replace(hour=21),
                "nb_personnes_requis": 2,
            },
        )
        self._seed_affectation(s4a.id, u1.membre_id, "SON")
        self._seed_affectation(s4b.id, u1.membre_id, "LUMIERE")

    def _seed_p5_technique_form(self, act_map, u1, d_jeu: datetime) -> None:
        """P5 — Session Technique Formation — BROUILLON — J+17. Couvre A2, C1 (0%)."""
        act = act_map.get("Session Technique Form")
        if not act:
            return
        plan, _ = self._get_or_create(
            PlanningService, activite_id=act.id, defaults={"statut_code": "BROUILLON"}
        )
        s5, _ = self._get_or_create(
            Slot,
            planning_id=plan.id,
            nom_creneau="Formation Vidéo & Streaming",
            defaults={
                "date_debut": d_jeu.replace(hour=19),
                "date_fin": d_jeu.replace(hour=22),
                "nb_personnes_requis": 2,
            },
        )
        self._seed_affectation(
            s5.id, u1.membre_id, "VIDEO", statut="PROPOSE", present=False
        )
        # s5b — nb_req=3, 0 affectation → rate=0% (C1 cas 3)
        self._get_or_create(
            Slot,
            planning_id=plan.id,
            nom_creneau="Équipement en Réserve",
            defaults={
                "date_debut": d_jeu.replace(hour=14),
                "date_fin": d_jeu.replace(hour=17),
                "nb_personnes_requis": 3,
            },
        )

    def _seed_p6_accueil(self, act_map, u2, d_dim1: datetime) -> None:
        """P6 — Permanence Accueil — PUBLIE — J+7. Couvre A1 (CONFIRME + PROPOSE)."""
        act = act_map.get("Permanence Accueil Culte")
        if not act:
            return
        plan, _ = self._get_or_create(
            PlanningService, activite_id=act.id, defaults={"statut_code": "PUBLIE"}
        )
        s6a, _ = self._get_or_create(
            Slot,
            planning_id=plan.id,
            nom_creneau="Accueil — Culte Matin",
            defaults={
                "date_debut": d_dim1.replace(hour=8, minute=30),
                "date_fin": d_dim1.replace(hour=11),
                "nb_personnes_requis": 2,
            },
        )
        s6b, _ = self._get_or_create(
            Slot,
            planning_id=plan.id,
            nom_creneau="Accueil — Culte Soir",
            defaults={
                "date_debut": d_dim1.replace(hour=17, minute=30),
                "date_fin": d_dim1.replace(hour=20),
                "nb_personnes_requis": 2,
            },
        )
        self._seed_affectation(s6a.id, u2.membre_id, "HOTE_ACCUEIL")
        self._seed_affectation(
            s6b.id, u2.membre_id, "HOTE_ACCUEIL", statut="PROPOSE", present=False
        )

    def _seed_p7_jeunesse(self, act_map, u2, d_sam: datetime) -> None:
        """P7 — Réunion Jeunesse — ANNULE — J+19. Couvre A3 (delete lève exception)."""
        act = act_map.get("Reunion Jeunesse")
        if not act:
            return
        plan, _ = self._get_or_create(
            PlanningService, activite_id=act.id, defaults={"statut_code": "ANNULE"}
        )
        s7, _ = self._get_or_create(
            Slot,
            planning_id=plan.id,
            nom_creneau="Session Ados du Mois",
            defaults={
                "date_debut": d_sam.replace(hour=14),
                "date_fin": d_sam.replace(hour=18),
                "nb_personnes_requis": 2,
            },
        )
        self._seed_affectation(
            s7.id, u2.membre_id, "ANIMATEUR_JEUNESSE", statut="PROPOSE", present=False
        )

    def _seed_p8_soiree_louange(self, act_map, u0, u1, d_dim2: datetime) -> None:
        """P8 — Soirée Louange Mensuelle — PUBLIE — J+14. Couvre B2, C1 (100%), C2."""
        act = act_map.get("Soiree Louange Mensuelle")
        if not act:
            return
        plan, _ = self._get_or_create(
            PlanningService, activite_id=act.id, defaults={"statut_code": "PUBLIE"}
        )
        s8, _ = self._get_or_create(
            Slot,
            planning_id=plan.id,
            nom_creneau="Louange du Soir",
            defaults={
                "date_debut": d_dim2.replace(hour=18),
                "date_fin": d_dim2.replace(hour=22),
                "nb_personnes_requis": 2,
            },
        )
        self._seed_affectation(s8.id, u0.membre_id, "TENOR")  # C2
        self._seed_affectation(s8.id, u1.membre_id, "PIANO")  # B2

    def _seed_planning_complet(self, act_map, users, today: datetime) -> None:
        self.logger.info("Génération multi-plannings avec slots et affectations...")

        d_dim1 = today + timedelta(days=7)
        d_mer = today + timedelta(days=10)
        d_dim2 = today + timedelta(days=14)
        d_jeu = today + timedelta(days=17)
        d_sam = today + timedelta(days=19)
        d_dim3 = today + timedelta(days=28)

        u0 = users[0]
        u1 = users[1] if len(users) > 1 else users[0]
        u2 = users[2] if len(users) > 2 else users[0]

        self._seed_p1_culte_dominical(act_map, u0, u1, d_dim1)
        self._seed_p2_repetition_chorale(act_map, u0, u1, d_mer)
        self._seed_p3_second_culte(act_map, u0, u1, d_dim3)
        self._seed_p4_technique_dim(act_map, u1, d_dim1)
        self._seed_p5_technique_form(act_map, u1, d_jeu)
        self._seed_p6_accueil(act_map, u2, d_dim1)
        self._seed_p7_jeunesse(act_map, u2, d_sam)
        self._seed_p8_soiree_louange(act_map, u0, u1, d_dim2)

    # --- AUTRES MÉTHODES ---

    def _seed_activites(self, cid, min_map: dict, today: datetime):
        """Crée les activités avec des dates cohérentes avec leurs slots de planning."""
        act_map = {}
        for a in ACTIVITES_DATA:
            min_nom = a.get("ministere_nom", "Louange et Adoration")
            ministere = min_map.get(min_nom)
            if not ministere:
                self.logger.warning(
                    f"Ministère '{min_nom}' introuvable pour '{a['type']}'"
                )
                continue
            jour = today + timedelta(days=a.get("day_offset", 7))
            act, _ = self._get_or_create(
                Activite,
                type=a["type"],
                defaults={
                    "campus_id": cid,
                    "lieu": a.get("lieu", "Lieu par défaut"),
                    "date_creation": today,
                    "date_debut": jour.replace(hour=a.get("heure_debut", 9)),
                    "date_fin": jour.replace(hour=a.get("heure_fin", 21)),
                    "ministere_organisateur_id": ministere.id,
                },
            )
            act_map[a["type"]] = act
        return act_map

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
        Les autres rôles : username = prenom.lower() du membre associé
        (MEMBRES_INFOS[i]),
        password = USER_PASSWORD pour tous.
        Retourne uniquement les utilisateurs non-superadmin (pour le seed membres).
        """
        users = []
        membre_idx = 0
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
            else:
                # username = prenom du membre correspondant (ex: "amos", "jean", "awa")
                username = MEMBRES_INFOS[membre_idx]["prenom"].lower()
                u, _ = self._get_or_create(
                    Utilisateur,
                    username=username,
                    defaults={
                        "password": get_password_hash(USER_PASSWORD),
                        "actif": True,
                    },
                )
                self._get_or_create(
                    AffectationRole, utilisateur_id=u.id, role_id=role.id
                )
                users.append(u)
                membre_idx += 1
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

# pylint: disable=too-many-lines
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
    CampusMinistereLink,
    CategorieRole,
    Chant,
    ChantCategorie,
    ChantContenu,
    Equipe,
    EquipeMembre,
    Indisponibilite,
    Membre,
    MembreCampusLink,
    MembreMinistereLink,
    MembrePoleLink,
    MembreRole,
    Ministere,
    Organisation,
    Permission,
    PlanningChantLink,
    PlanningService,
    PlanningTemplate,
    PlanningTemplateRole,
    PlanningTemplateRoleMembre,
    PlanningTemplateSlot,
    Pole,
    Responsabilite,
    Role,
    RoleCompetence,
    RolePermission,
    Slot,
    StatutAffectation,
    StatutPlanning,
    TypeResponsabilite,
    Utilisateur,
)
from models.schema_db_model import MinistereRoleConfig

from .data import (
    ACTIVITES_CUGNAUX,
    ACTIVITES_DATA,
    CATEGORIES_ROLES,
    DEMO_MEMBRE_INFO,
    DEMO_PASSWORD,
    DEMO_USERNAME,
    EQUIPE_MEMBRES_DATA,
    EQUIPES_DATA,
    MEMBRES_INFOS,
    MINISTERE_ROLES_CONFIG,
    MINISTERES_DATA,
    PERMISSIONS,
    PLANNING_TEMPLATES_SEED,
    POLES_DATA,
    RESPONSABILITES_DATA,
    ROLES,
    ROLES_COMPETENCES,
    SEED_CAMPUS,
    SEED_ORGANISATIONS,
    SONGBOOK_CATEGORIES,
    SONGBOOK_CHANTS,
    STATUTS_PLANNING,
    SUPERADMIN_PASSWORD,
    SUPERADMIN_USERNAME,
    TYPES_RESPONSABILITE,
    USER_PASSWORD,
    MembreInfo,
)
from .data_extra import (
    INDISPONIBILITES_SEED,
    MEMBRES_SUPPLEMENTAIRES,
    IndisponibiliteData,
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
                campus_map = self._seed_campus(org_map)
                campus_paris = campus_map["Campus Toulouse"]

                # 2. RBAC & SÉCURITÉ
                role_map = self._seed_roles(ROLES)
                perm_map = self._seed_permissions(PERMISSIONS)
                self._seed_role_permissions(role_map, PERMISSIONS, perm_map)
                user_list = self._seed_users_for_roles(role_map)

                # Lier le superadmin à tous les campus (fix chicken-and-egg)
                sa_user = self.db.exec(
                    select(Utilisateur).where(
                        Utilisateur.username == SUPERADMIN_USERNAME
                    )
                ).first()
                if sa_user:
                    self._seed_superadmin_membre(str(sa_user.id), campus_map)

                # 3. RÉFÉRENTIELS MÉTIER
                self._seed_categories_et_roles()
                self._seed_referentiels_fixes()

                min_map = self._seed_ministeres(campus_map=campus_map)
                self._seed_ministere_role_configs(min_map)
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
                demo_user = self._seed_demo_user(
                    role_map, campus_map, min_map, pole_map
                )
                self._seed_membres_supplementaires(campus_map, min_map, pole_map)

                # 5. OPÉRATIONNEL & PLANNING (Cœur de la modification)
                eq_map = self._seed_equipes(min_map)
                self._seed_equipe_membres(eq_map, user_list)
                self._seed_responsabilites(user_list, min_map, pole_map)
                self._seed_planning_complet(act_map, user_list, today)
                if demo_user:
                    self._seed_demo_planning(act_map, demo_user, today)

                # 6. SONGBOOK
                self._seed_songbook(campus_paris.id)

                # 6b. RÉPERTOIRE : attacher des chants aux plannings
                self._seed_planning_repertoire(campus_paris.id, act_map)

                # 7. PLANNING TEMPLATES
                self._seed_planning_templates(campus_paris.id, min_map, user_list)

                # 8. ACTIVITÉS CUGNAUX
                self._seed_activites_cugnaux(
                    campus_map["Campus Cugnaux"].id, min_map, today
                )

                # 9. INDISPONIBILITÉS
                self._seed_indisponibilites()

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

    def _seed_organisations(self) -> dict:
        # First pass: create all orgs without parent_id
        org_map: dict = {}
        for d in SEED_ORGANISATIONS:
            org, _ = self._get_or_create(
                Organisation,
                nom=d["nom"],
                defaults={"date_creation": d["date_creation"]},
            )
            org_map[d["nom"]] = org
        # Second pass: assign parent_id
        for d in SEED_ORGANISATIONS:
            if d.get("parent_nom"):
                parent = org_map[d["parent_nom"]]
                org = org_map[d["nom"]]
                if org.parent_id != parent.id:
                    org.parent_id = parent.id
                    self.db.add(org)
        return org_map

    def _seed_campus(self, org_map: dict) -> dict:
        return {
            d["nom"]: self._get_or_create(
                Campus,
                nom=d["nom"],
                defaults={
                    "organisation_id": org_map[d["org_nom"]].id,
                    "ville": d["ville"],
                    "pays": d["pays"],
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

    def _seed_ministere_role_configs(self, min_map: dict[str, Ministere]) -> None:
        """Active les rôles par ministère (t_ministere_role_config)."""
        for entry in MINISTERE_ROLES_CONFIG:
            ministere = min_map.get(str(entry["ministere_nom"]))
            if not ministere:
                continue
            for role_code in entry["role_codes"]:
                self._get_or_create(
                    MinistereRoleConfig,
                    ministere_id=str(ministere.id),
                    role_code=str(role_code),
                )

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
        for c_name in info.get("campus_names") or ["Campus Toulouse"]:
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

    def _seed_superadmin_membre(self, utilisateur_id: str, campus_map: dict) -> None:
        """
        Crée un Membre minimal pour le superadmin et le lie à tous les campus.
        Idempotent — ne fait rien si le lien Utilisateur→Membre existe déjà.
        """
        user = self.db.get(Utilisateur, utilisateur_id)
        if not user or user.membre_id:
            return
        membre, _ = self._get_or_create(
            Membre,
            email="superadmin@mla-planner.com",
            defaults={"nom": "Admin", "prenom": "Super", "actif": True},
        )
        user.membre_id = membre.id
        self.db.add(user)
        self.db.flush()
        campuses = list(campus_map.values())
        for campus in campuses:
            self._get_or_create(
                MembreCampusLink, membre_id=membre.id, campus_id=campus.id
            )
        if campuses and not membre.campus_principal_id:
            membre.campus_principal_id = campuses[0].id
            self.db.add(membre)
            self.db.flush()

    def _seed_users_for_roles(self, rm):
        """
        Crée les utilisateurs techniques pour chaque rôle.
        Le SUPER_ADMIN a un compte fixe. Son Membre est créé via
        _seed_superadmin_membre (appelé après la construction de campus_map).
        Les autres rôles : username = prenom.lower() du membre associé
        (MEMBRES_INFOS[i]), password = USER_PASSWORD pour tous.
        Retourne uniquement les utilisateurs non-superadmin (pour le seed membres).
        """
        users = []
        membre_idx = 0
        for rn, role in rm.items():
            if rn == "Super Admin":
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

    def _seed_demo_user(
        self,
        role_map: dict,
        campus_map: dict,
        min_map: dict,
        pole_map: dict,
    ) -> Utilisateur | None:
        """Crée le compte démo (Membre MLA, lecture seule, idempotent)."""
        self.logger.info("🎭 Compte démo...")
        membre_mla_role = role_map.get("Membre MLA")
        if not membre_mla_role:
            return None
        user, _ = self._get_or_create(
            Utilisateur,
            username=DEMO_USERNAME,
            defaults={
                "password": get_password_hash(DEMO_PASSWORD),
                "actif": True,
            },
        )
        self._get_or_create(
            AffectationRole, utilisateur_id=user.id, role_id=membre_mla_role.id
        )
        membre, _ = self._get_or_create(
            Membre,
            email=DEMO_MEMBRE_INFO["email"],
            defaults={
                "nom": DEMO_MEMBRE_INFO["nom"],
                "prenom": DEMO_MEMBRE_INFO["prenom"],
                "actif": True,
            },
        )
        if not user.membre_id:
            user.membre_id = membre.id
            self.db.add(user)
            self.db.flush()
        self._link_member_to_entities(
            membre.id,
            DEMO_MEMBRE_INFO,
            c_map=campus_map,
            m_map=min_map,
            p_map=pole_map,
        )
        self._assign_member_roles(membre.id, DEMO_MEMBRE_INFO.get("roles") or [])
        campus_names = DEMO_MEMBRE_INFO.get("campus_names") or []
        if campus_names and campus_names[0] in campus_map:
            principal_id = campus_map[campus_names[0]].id
            if membre.campus_principal_id != principal_id:
                membre.campus_principal_id = principal_id
                self.db.add(membre)
                self.db.flush()
        return user

    def _upsert_slot(
        self,
        *,
        planning_id: str,
        nom_creneau: str,
        date_debut: datetime,
        date_fin: datetime,
        nb_personnes_requis: int,
    ) -> Slot:
        """Crée ou met à jour les dates d'un slot (dates toujours relatives à today)."""
        slot, created = self._get_or_create(
            Slot,
            planning_id=planning_id,
            nom_creneau=nom_creneau,
            defaults={
                "date_debut": date_debut,
                "date_fin": date_fin,
                "nb_personnes_requis": nb_personnes_requis,
            },
        )
        if not created:
            slot.date_debut = date_debut
            slot.date_fin = date_fin
            self.db.add(slot)
            self.db.flush()
        return slot

    def _seed_demo_planning(
        self, act_map: dict, demo_user: Utilisateur, today: datetime
    ) -> None:
        """Affecte le compte démo à 3 ministères avec des dates toujours à jour."""
        if not demo_user.membre_id:
            return
        demo_id = str(demo_user.membre_id)
        d_j0 = today
        d_j2 = today + timedelta(days=2)
        d_j3 = today + timedelta(days=3)
        d_dim = today + timedelta(days=7)
        d_mer = today + timedelta(days=10)
        d_sam = today + timedelta(days=19)

        self._seed_demo_j0(act_map, demo_id, d_j0)
        self._seed_demo_j2(act_map, demo_id, d_j2)
        self._seed_demo_j3(act_map, demo_id, d_j3)
        self._seed_demo_accueil(act_map, demo_id, d_dim)
        self._seed_demo_louange(act_map, demo_id, d_mer)
        self._seed_demo_jeunesse(act_map, demo_id, d_sam)
        self._seed_demo_affectations_extra(act_map, demo_id, d_dim)
        self._seed_demo_indisponibilites(demo_id, today)

    def _seed_demo_j0(self, act_map: dict, demo_id: str, d_j0: datetime) -> None:
        """3 activités aujourd'hui (J+0) — une par ministère, heures distinctes."""
        # Accueil — 9h-11h
        act_acc = act_map.get("Permanence Accueil Culte")
        if act_acc:
            plan_acc, _ = self._get_or_create(
                PlanningService,
                activite_id=act_acc.id,
                defaults={"statut_code": "PUBLIE"},
            )
            slot_acc = self._upsert_slot(
                planning_id=str(plan_acc.id),
                nom_creneau="Accueil Démo — Matin J0",
                date_debut=d_j0.replace(hour=9),
                date_fin=d_j0.replace(hour=11),
                nb_personnes_requis=2,
            )
            self._seed_affectation(str(slot_acc.id), demo_id, "HOTE_ACCUEIL")
        # Louange — 14h-16h30
        act_lou = act_map.get("Culte Dominical")
        if act_lou:
            plan_lou, _ = self._get_or_create(
                PlanningService,
                activite_id=act_lou.id,
                defaults={"statut_code": "PUBLIE"},
            )
            slot_lou = self._upsert_slot(
                planning_id=str(plan_lou.id),
                nom_creneau="Louange Démo — Après-midi J0",
                date_debut=d_j0.replace(hour=14),
                date_fin=d_j0.replace(hour=16, minute=30),
                nb_personnes_requis=3,
            )
            self._seed_affectation(
                str(slot_lou.id), demo_id, "TENOR", statut="CONFIRME"
            )
        # Jeunesse — 18h-20h
        act_jeu = act_map.get("Reunion Jeunesse")
        if act_jeu:
            plan_jeu, _ = self._get_or_create(
                PlanningService,
                activite_id=act_jeu.id,
                defaults={"statut_code": "PUBLIE"},
            )
            slot_jeu = self._upsert_slot(
                planning_id=str(plan_jeu.id),
                nom_creneau="Jeunesse Démo — Soir J0",
                date_debut=d_j0.replace(hour=18),
                date_fin=d_j0.replace(hour=20),
                nb_personnes_requis=2,
            )
            self._seed_affectation(
                str(slot_jeu.id), demo_id, "ANIMATEUR_JEUNESSE", statut="PROPOSE"
            )

    def _seed_demo_j2(self, act_map: dict, demo_id: str, d_j2: datetime) -> None:
        act = act_map.get("Permanence Accueil Culte")
        if not act:
            return
        plan, _ = self._get_or_create(
            PlanningService, activite_id=act.id, defaults={"statut_code": "PUBLIE"}
        )
        slot = self._upsert_slot(
            planning_id=str(plan.id),
            nom_creneau="Accueil Démo — Préparation J+2",
            date_debut=d_j2.replace(hour=8),
            date_fin=d_j2.replace(hour=10),
            nb_personnes_requis=2,
        )
        self._seed_affectation(str(slot.id), demo_id, "HOTE_ACCUEIL", statut="CONFIRME")

    def _seed_demo_j3(self, act_map: dict, demo_id: str, d_j3: datetime) -> None:
        act = act_map.get("Culte Dominical")
        if not act:
            return
        plan, _ = self._get_or_create(
            PlanningService, activite_id=act.id, defaults={"statut_code": "PUBLIE"}
        )
        slot = self._upsert_slot(
            planning_id=str(plan.id),
            nom_creneau="Louange Démo — Répétition J+3",
            date_debut=d_j3.replace(hour=19),
            date_fin=d_j3.replace(hour=21),
            nb_personnes_requis=3,
        )
        self._seed_affectation(str(slot.id), demo_id, "TENOR", statut="PROPOSE")

    def _seed_demo_accueil(self, act_map: dict, demo_id: str, d_dim: datetime) -> None:
        act = act_map.get("Permanence Accueil Culte")
        if not act:
            return
        plan, _ = self._get_or_create(
            PlanningService, activite_id=act.id, defaults={"statut_code": "PUBLIE"}
        )
        slot = self._upsert_slot(
            planning_id=str(plan.id),
            nom_creneau="Accueil Démo — Culte Matin",
            date_debut=d_dim.replace(hour=8, minute=30),
            date_fin=d_dim.replace(hour=11),
            nb_personnes_requis=2,
        )
        self._seed_affectation(str(slot.id), demo_id, "HOTE_ACCUEIL")

    def _seed_demo_louange(self, act_map: dict, demo_id: str, d_mer: datetime) -> None:
        act = act_map.get("Repetition Chorale")
        if not act:
            return
        plan, _ = self._get_or_create(
            PlanningService, activite_id=act.id, defaults={"statut_code": "PUBLIE"}
        )
        slot = self._upsert_slot(
            planning_id=str(plan.id),
            nom_creneau="Louange Démo — Répétition Chorale",
            date_debut=d_mer.replace(hour=19),
            date_fin=d_mer.replace(hour=21, minute=30),
            nb_personnes_requis=3,
        )
        self._seed_affectation(str(slot.id), demo_id, "TENOR", statut="PROPOSE")

    def _seed_demo_jeunesse(self, act_map: dict, demo_id: str, d_sam: datetime) -> None:
        act = act_map.get("Reunion Jeunesse")
        if not act:
            return
        plan, _ = self._get_or_create(
            PlanningService, activite_id=act.id, defaults={"statut_code": "PUBLIE"}
        )
        slot = self._upsert_slot(
            planning_id=str(plan.id),
            nom_creneau="Jeunesse Démo — Session Ados",
            date_debut=d_sam.replace(hour=14),
            date_fin=d_sam.replace(hour=18),
            nb_personnes_requis=2,
        )
        self._seed_affectation(
            str(slot.id), demo_id, "ANIMATEUR_JEUNESSE", statut="CONFIRME"
        )

    def _seed_demo_affectations_extra(
        self, act_map: dict, demo_id: str, d_dim: datetime
    ) -> None:
        """Ajoute demo dans des slots existants : Louange Soir + Soirée Louange."""
        act_cd = act_map.get("Culte Dominical")
        if act_cd:
            plan_cd = self.db.exec(
                select(PlanningService).where(PlanningService.activite_id == act_cd.id)
            ).first()
            if plan_cd:
                slot_soir = self.db.exec(
                    select(Slot).where(
                        Slot.planning_id == plan_cd.id,
                        Slot.nom_creneau == "Équipe Louange Soir",
                    )
                ).first()
                if slot_soir:
                    self._seed_affectation(
                        str(slot_soir.id), demo_id, "TENOR", statut="PROPOSE"
                    )
        act_sl = act_map.get("Soiree Louange Mensuelle")
        if act_sl:
            plan_sl = self.db.exec(
                select(PlanningService).where(PlanningService.activite_id == act_sl.id)
            ).first()
            if plan_sl:
                slot_louange = self.db.exec(
                    select(Slot).where(
                        Slot.planning_id == plan_sl.id,
                        Slot.nom_creneau == "Louange du Soir",
                    )
                ).first()
                if slot_louange:
                    self._seed_affectation(str(slot_louange.id), demo_id, "ALTO")

    def _seed_demo_indisponibilites(self, demo_id: str, today: datetime) -> None:
        """Crée des indisponibilités démo avec dates relatives à today (upsert)."""
        indispos = [
            {
                "motif": "Weekend famille",
                "date_debut": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
                "date_fin": (today + timedelta(days=32)).strftime("%Y-%m-%d"),
                "validee": True,
            },
            {
                "motif": "Formation musicale",
                "date_debut": (today + timedelta(days=45)).strftime("%Y-%m-%d"),
                "date_fin": (today + timedelta(days=47)).strftime("%Y-%m-%d"),
                "validee": False,
            },
            {
                "motif": "Déplacement professionnel",
                "date_debut": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
                "date_fin": (today + timedelta(days=63)).strftime("%Y-%m-%d"),
                "validee": True,
            },
        ]
        for data in indispos:
            self._upsert_demo_indisponibilite(demo_id, data)

    def _upsert_demo_indisponibilite(self, membre_id: str, data: dict) -> None:
        """Crée ou met à jour une indisponibilité démo (clé: membre_id + motif)."""
        existing = self.db.exec(
            select(Indisponibilite).where(
                Indisponibilite.membre_id == membre_id,
                Indisponibilite.motif == data["motif"],
            )
        ).first()
        if existing:
            existing.date_debut = data["date_debut"]
            existing.date_fin = data["date_fin"]
            existing.validee = data["validee"]
            self.db.add(existing)
            self.db.flush()
        else:
            indispo = Indisponibilite(
                membre_id=membre_id,
                date_debut=data["date_debut"],
                date_fin=data["date_fin"],
                motif=data["motif"],
                validee=data["validee"],
            )
            self.db.add(indispo)
            self.db.flush()

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

    # --- PLANNING TEMPLATES ---

    def _seed_planning_templates(
        self,
        campus_id: str,
        min_map: dict,
        users: list,
    ) -> None:
        """Seed des templates de planning réutilisables (idempotent)."""
        creator_id: str = users[0].membre_id if users else ""
        if not creator_id:
            self.logger.warning("Aucun créateur pour les templates — ignoré.")
            return
        for tpl_data in PLANNING_TEMPLATES_SEED:
            ministere = min_map.get(tpl_data["ministere_nom"])
            if not ministere:
                self.logger.warning(
                    "Ministère '%s' introuvable — template ignoré.",
                    tpl_data["ministere_nom"],
                )
                continue
            tpl, created = self._get_or_create(
                PlanningTemplate,
                nom=tpl_data["nom"],
                campus_id=campus_id,
                defaults={
                    "description": tpl_data["description"],
                    "activite_type": tpl_data["activite_type"],
                    "duree_minutes": tpl_data["duree_minutes"],
                    "ministere_id": ministere.id,
                    "created_by_id": creator_id,
                },
            )
            if created:
                self._seed_template_slots(tpl.id, tpl_data["slots"])

    def _seed_template_slots(
        self,
        template_id: str,
        slots_data: list,
    ) -> None:
        """Crée les slots d'un template avec leurs rôles (idempotent)."""
        for s in slots_data:
            slot, _ = self._get_or_create(
                PlanningTemplateSlot,
                template_id=template_id,
                nom_creneau=s["nom_creneau"],
                defaults={
                    "offset_debut_minutes": s["offset_debut_minutes"],
                    "offset_fin_minutes": s["offset_fin_minutes"],
                    "nb_personnes_requis": s["nb_personnes_requis"],
                },
            )
            for role_data in s["roles"]:
                role, _ = self._get_or_create(
                    PlanningTemplateRole,
                    slot_id=slot.id,
                    role_code=role_data["role_code"],
                )
                self._seed_template_role_membres(
                    role.id,
                    role_data.get("membres_suggeres_ids", []),
                )

    def _seed_template_role_membres(self, role_id: str, membre_ids: list) -> None:
        """Crée les membres suggérés d'un rôle de template (idempotent)."""
        for membre_id in membre_ids:
            if self.db.get(Membre, membre_id) is None:
                continue
            self._get_or_create(
                PlanningTemplateRoleMembre,
                template_role_id=role_id,
                membre_id=membre_id,
            )

    # --- MEMBRES SUPPLÉMENTAIRES ---

    def _seed_membre_simple(
        self,
        info: MembreInfo,
        *,
        campus_map: dict,
        min_map: dict,
        pole_map: dict,
    ) -> None:
        """Crée un membre sans compte Utilisateur (idempotent)."""
        membre, _ = self._get_or_create(
            Membre,
            email=info["email"],
            defaults={
                "nom": info["nom"],
                "prenom": info["prenom"],
                "actif": True,
            },
        )
        self._link_member_to_entities(
            membre.id, info, c_map=campus_map, m_map=min_map, p_map=pole_map
        )
        self._assign_member_roles(membre.id, info.get("roles") or [])
        campus_names = info.get("campus_names") or []
        if campus_names and campus_names[0] in campus_map:
            principal_id = campus_map[campus_names[0]].id
            if membre.campus_principal_id != principal_id:
                membre.campus_principal_id = principal_id
                self.db.add(membre)
                self.db.flush()

    def _seed_membres_supplementaires(
        self, campus_map: dict, min_map: dict, pole_map: dict
    ) -> None:
        """Seed les 57 membres supplémentaires sans compte Utilisateur."""
        self.logger.info(
            "👥 Membres supplémentaires (%d)...", len(MEMBRES_SUPPLEMENTAIRES)
        )
        for info in MEMBRES_SUPPLEMENTAIRES:
            self._seed_membre_simple(
                info, campus_map=campus_map, min_map=min_map, pole_map=pole_map
            )

    # --- ACTIVITÉS TOULOUSE ---

    def _seed_activites_cugnaux(
        self, campus_id: str, min_map: dict, today: datetime
    ) -> None:
        """Seed les activités du Campus Cugnaux."""
        self.logger.info("📅 Activités Cugnaux...")
        for a in ACTIVITES_CUGNAUX:
            min_nom = a.get("ministere_nom", "Louange et Adoration")
            ministere = min_map.get(min_nom)
            if not ministere:
                continue
            jour = today + timedelta(days=a.get("day_offset", 7))
            self._get_or_create(
                Activite,
                type=a["type"],
                defaults={
                    "campus_id": campus_id,
                    "lieu": a.get("lieu", "Lieu par défaut"),
                    "date_creation": today,
                    "date_debut": jour.replace(hour=a.get("heure_debut", 9)),
                    "date_fin": jour.replace(hour=a.get("heure_fin", 21)),
                    "ministere_organisateur_id": ministere.id,
                },
            )

    # --- INDISPONIBILITÉS ---

    def _seed_indisponibilites(self) -> None:
        """Seed les indisponibilités des membres (idempotent)."""
        self.logger.info("🚫 Indisponibilités (%d)...", len(INDISPONIBILITES_SEED))
        for data in INDISPONIBILITES_SEED:
            self._seed_one_indisponibilite(data)

    def _seed_one_indisponibilite(self, data: IndisponibiliteData) -> None:
        """Crée une indisponibilité pour un membre identifié par email."""
        membre = self.db.exec(
            select(Membre).where(Membre.email == data["membre_email"])
        ).first()
        if not membre:
            self.logger.warning(
                "Membre '%s' introuvable — indisponibilité ignorée.",
                data["membre_email"],
            )
            return
        self._get_or_create(
            Indisponibilite,
            membre_id=membre.id,
            date_debut=data["date_debut"],
            date_fin=data["date_fin"],
            defaults={
                "motif": data.get("motif"),
                "validee": data.get("validee", False),
            },
        )

    # --- SONGBOOK ---

    def _seed_songbook(self, campus_id: str) -> None:
        """Seed categories et chants ChordPro pour le module Songbook."""
        self._seed_chant_categories()
        self._seed_chants(campus_id)

    def _seed_chant_categories(self) -> None:
        """Crée les catégories de chants (idempotent via code PK)."""
        for cat in SONGBOOK_CATEGORIES:
            self._get_or_create(
                ChantCategorie,
                code=cat["code"],
                defaults={
                    "libelle": cat["libelle"],
                    "ordre": cat["ordre"],
                },
            )

    def _seed_chants(self, campus_id: str) -> None:
        """Crée les chants avec leur contenu ChordPro."""
        for data in SONGBOOK_CHANTS:
            chant, _ = self._get_or_create(
                Chant,
                titre=data["titre"],
                campus_id=campus_id,
                defaults={
                    "artiste": data["artiste"],
                    "categorie_code": data["categorie_code"],
                    "youtube_url": data["youtube_url"],
                    "actif": True,
                },
            )
            self._get_or_create(
                ChantContenu,
                chant_id=chant.id,
                defaults={
                    "tonalite": data["tonalite"],
                    "paroles_chords": data["paroles_chords"],
                    "version": 1,
                },
            )

    def _seed_planning_repertoire(self, campus_id: str, act_map: dict) -> None:
        """Attache les 3 premiers chants du campus au premier planning Louange."""
        louange_key = next((k for k in act_map if "louange" in k.lower()), None)
        if not louange_key:
            return
        act = act_map[louange_key]
        planning = self.db.exec(
            select(PlanningService)
            .where(PlanningService.activite_id == act.id)
            .where(PlanningService.deleted_at == None)  # noqa: E711
        ).first()
        if not planning:
            return

        chants = self.db.exec(
            select(Chant).where(Chant.campus_id == campus_id).limit(3)
        ).all()

        for ordre, chant in enumerate(chants):
            self._get_or_create(
                PlanningChantLink,
                planning_id=planning.id,
                chant_id=chant.id,
                defaults={"ordre": ordre},
            )

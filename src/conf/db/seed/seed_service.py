import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional, Type, TypeVar

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, SQLModel, select

from core.auth.security import get_password_hash
from mla_enum import VoixEnum
from models import (
    Activite,
    Affectation,
    AffectationContexte,
    AffectationRole,
    Campus,
    Chantre,
    Choriste,
    Equipe,
    Equipe_Membre,
    Indisponibilite,
    Instrument,
    Membre,
    Ministere,
    Musicien,
    OrganisationICC,
    Pays,
    Permission,
    PlanningService,
    Pole,
    Responsabilite,
    Role,
    RolePermission,
    StatutPlanning,
    TypeResponsabilite,
    Utilisateur,
    Voix,
)
from models.schema_db_model import ChoristeVoix, MusicienInstrument

from .data import (
    ACTIVITES_DATA,
    EQUIPE_MEMBRES_DATA,
    EQUIPES_DATA,
    INSTRUMENTS_DATA,
    MEMBRES_INFOS,
    MINISTERES_DATA,
    PERMISSIONS,
    POLES_DATA,
    RESPONSABILITES_DATA,
    ROLES,
    SEED_CAMPUS,
    SEED_ORGANISATIONS,
    SEED_PAYS,
    STATUTS_PLANNING,
    TYPES_RESPONSABILITE,
    VOIX_DATA,
)

T = TypeVar("T", bound=SQLModel)


class SeedService:
    def __init__(self, db: Session, logger: logging.Logger | None = None):
        self.db = db
        self.logger = logger or logging.getLogger("seed_service")

    def run(self):
        self.logger.info("🚀 Lancement du Seed Master Expert...")
        try:
            with self.db.begin():
                # 1. GÉOGRAPHIE
                org_map = self._seed_organisations()
                pays_map = self._seed_pays(org_map)
                campus_map = self._seed_campus(pays_map)
                campus_id = campus_map["Campus Paris"].id

                # 2. RBAC (Utilisateurs & Roles)
                role_map = self._seed_roles(ROLES)
                perm_map = self._seed_permissions(PERMISSIONS)
                self._seed_role_permissions(role_map, PERMISSIONS, perm_map)
                user_list = self._seed_users_for_roles(role_map)

                # 3. RÉFÉRENTIELS ET STRUCTURES
                self._seed_voix()
                instr_map = self._seed_referentiels()
                min_map = self._seed_ministeres(campus_id)
                pole_map = self._seed_poles(min_map)
                act_map = self._seed_activites(campus_id)

                # 4. RH & SPÉCIALISATIONS
                chantre_objs = self._seed_rh_complet(
                    user_list, min_map, pole_map, instr_map
                )

                # 5. OPÉRATIONNEL (Remplissage des tables manquantes)
                eq_map = self._seed_equipes(min_map)
                self._seed_equipe_membres(eq_map, user_list)
                self._seed_responsabilites(user_list, min_map, pole_map)
                self._seed_planning_et_affectations(act_map, chantre_objs)
                self._seed_indisponibilites(chantre_objs)

                # 6. CONTEXTES (Pour le fonctionnement de l'app)
                self._seed_affectation_contextes(user_list, min_map, pole_map)

            self.logger.info(
                "✅ Toutes les tables (incluant les tables de liaison) sont alimentées !"
            )
        except SQLAlchemyError as e:
            self.logger.error(f"❌ Erreur critique: {str(e)}")
            raise

    # --- NOUVELLES MÉTHODES POUR TABLES MANQUANTES ---

    def _seed_equipe_membres(self, eq_map, user_list):
        self.logger.info("🔗 Remplissage de t_equipe_membre...")
        for data in EQUIPE_MEMBRES_DATA:
            equipe = eq_map.get(data["equipe_nom"])
            user = user_list[data["user_index"]]
            if equipe and user.membre_id:
                self._get_or_create(
                    Equipe_Membre, equipe_id=equipe.id, membre_id=user.membre_id
                )

    def _seed_responsabilites(self, user_list, min_map, pole_map):
        self.logger.info("🎖️ Remplissage de t_responsabilite...")
        for res in RESPONSABILITES_DATA:
            user = user_list[res["user_index"]]
            self._get_or_create(
                Responsabilite,
                membre_id=user.membre_id,
                type_code=res["type"],
                defaults={
                    "ministere_id": min_map[res["ministere"]].id,
                    "pole_id": pole_map[res["pole"]].id,
                    "dateDebut": datetime.now().isoformat(),
                },
            )

    def _seed_affectation_contextes(self, user_list, min_map, pole_map):
        self.logger.info("🔐 Remplissage de t_affectation_contexte (RBAC)...")
        # On donne un contexte au Responsable (index 1) sur le Ministère Louange
        resp_user = user_list[1]
        stmt = select(AffectationRole).where(
            AffectationRole.utilisateur_id == resp_user.id
        )
        aff_role = self.db.exec(stmt).first()

        if aff_role:
            self._get_or_create(
                AffectationContexte,
                affectation_role_id=aff_role.id,
                defaults={
                    "ministere_id": min_map["Louange et Adoration"].id,
                    "pole_id": pole_map["Chorale"].id,
                },
            )

    # --- MÉTHODES EXISTANTES CORRIGÉES ---

    def _get_or_create(
        self,
        model: Type[T],
        defaults: Optional[dict[str, Any]] = None,  # Correction ici
        **filters: Any,
    ) -> tuple[T, bool]:
        stmt = select(model).filter_by(**filters)
        instance = self.db.exec(stmt).first()

        if instance:
            return instance, False

        # On prépare les données d'initialisation
        params = {**filters}
        if defaults:
            params.update(defaults)

        obj = model(**params)
        self.db.add(obj)
        self.db.flush()

        return obj, True

    def _seed_rh_complet(self, users, min_map, pole_map, instr_map):
        chantres = []
        self.logger.info(
            "👥 Remplissage RH (Membres, Chantres, Choristes, Musiciens)..."
        )

        for i, user in enumerate(users):
            info = MEMBRES_INFOS[i % len(MEMBRES_INFOS)]

            # On force tout le monde dans la Louange pour le seed
            # afin de s'assurer d'avoir des Musiciens/Choristes
            m_nom = "Louange et Adoration"
            p_nom = "Chorale" if i % 2 == 0 else "Musiciens"

            # 1. Création du Membre
            membre, _ = self._get_or_create(
                Membre,
                email=info["email"],
                defaults={
                    "nom": info["nom"],
                    "prenom": info["prenom"],
                    "telephone": f"012345678{i}",
                    "ministere_id": min_map[m_nom].id,
                    "pole_id": pole_map[p_nom].id,
                    "date_inscription": datetime.now().date(),
                    "actif": True,
                },
            )

            # Mise à jour de l'utilisateur avec l'ID du membre
            user.membre_id = membre.id
            self.db.add(user)
            self.db.flush()

            # 2. Création systématique du Chantre pour la Louange
            chantre, _ = self._get_or_create(
                Chantre,
                membre_id=membre.id,
                defaults={
                    "niveau": "Intermédiaire",
                    "date_integration": datetime.now().date(),
                },
            )
            chantres.append(chantre)

            # 3. Répartition : Pair = Choriste, Impair = Musicien
            if i % 2 == 0:
                self.logger.info(f"🎤 Création Choriste pour {info['nom']}")
                self._create_choriste_specialization(chantre.id)
            else:
                self.logger.info(f"🎸 Création Musicien pour {info['nom']}")
                self._create_musicien_specialization(chantre.id, instr_map)

        return chantres

    def _create_choriste_specialization(self, chantre_id: uuid.UUID):
        """Sous-méthode pour gérer la création de la partie choriste."""
        choriste, created = self._get_or_create(Choriste, chantre_id=chantre_id)
        if created:
            self._get_or_create(
                ChoristeVoix,
                choriste_id=choriste.id,
                voix_code=VoixEnum.TENOR,
                defaults={"is_principal": True},
            )

    def _create_musicien_specialization(self, chantre_id: uuid.UUID, instr_map: dict):
        """Sous-méthode corrigée pour garantir l'insertion en table de liaison."""
        musicien, _ = self._get_or_create(Musicien, chantre_id=chantre_id)

        # On essaie de récupérer le Piano ou le premier instrument disponible
        piano_obj = instr_map.get("PIANO") or list(instr_map.values())[0]

        if piano_obj:
            # On utilise get_or_create pour éviter les doublons sur la table de liaison
            self._get_or_create(
                MusicienInstrument,
                musicien_id=musicien.id,
                instrument_id=piano_obj.id,
                defaults={"is_principal": True},
            )
            self.logger.info(
                f"✅ Liaison Musicien-Instrument créée (ID: {piano_obj.id})"
            )

    def _seed_equipes(self, mm):
        eq_map = {}
        for mn, eqs in EQUIPES_DATA.items():
            for eq_nom in eqs:
                obj, _ = self._get_or_create(Equipe, nom=eq_nom, ministere_id=mm[mn].id)
                eq_map[eq_nom] = obj
        return eq_map

    # (Gardez les autres méthodes _seed_organisations, _seed_pays)
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
                    "ville": d["ville"],
                    "timezone": d["timezone"],
                    "pays_id": pays_map[d["pays_nom"]].id,
                },
            )[0]
            for d in SEED_CAMPUS
        }

    def _seed_referentiels(self):
        self.logger.info("🎹 Remplissage des référentiels instruments...")
        instr_map = {}
        for inst_nom in INSTRUMENTS_DATA:
            # On normalise le code comme le fait le validateur
            code = inst_nom.strip().upper().replace(" ", "_")
            obj, _ = self._get_or_create(
                Instrument, code=code, defaults={"nom": inst_nom}
            )
            instr_map[code] = obj

        for stat in STATUTS_PLANNING:
            self._get_or_create(StatutPlanning, code=stat)
        for resp in TYPES_RESPONSABILITE:
            self._get_or_create(TypeResponsabilite, code=resp)

        return instr_map  # On retourne la map pour usage ultérieur

    def _seed_ministeres(self, campus_id):
        return {
            m["nom"]: self._get_or_create(
                Ministere,
                nom=m["nom"],
                campus_id=campus_id,
                defaults={"date_creation": m["date_creation"], "actif": m["actif"]},
            )[0]
            for m in MINISTERES_DATA
        }

    def _seed_poles(self, min_map):
        p_map = {}
        for m_nom, poles in POLES_DATA.items():
            for p in poles:
                pole, _ = self._get_or_create(
                    Pole,
                    nom=p["nom"],
                    ministere_id=min_map[m_nom].id,
                    defaults={"description": p["description"], "active": p["active"]},
                )
                p_map[p["nom"]] = pole
        return p_map

    def _seed_indisponibilites(self, chantre_objs):
        if not chantre_objs:
            return
        self._get_or_create(
            Indisponibilite,
            chantre_id=chantre_objs[0].id,
            dateDebut=(datetime.now() + timedelta(days=1)).isoformat(),
            defaults={
                "dateFin": (datetime.now() + timedelta(days=2)).isoformat(),
                "motif": "Congés",
                "validee": True,
            },
        )

    def _seed_planning_et_affectations(self, act_map, chantres):
        if not act_map.get("Culte") or not chantres:
            return
        plan, _ = self._get_or_create(
            PlanningService, activite_id=act_map["Culte"].id, statut_code="PUBLIE"
        )
        for ch in chantres[:2]:
            self._get_or_create(
                Affectation,
                planning_id=plan.id,
                chantre_id=ch.id,
                defaults={"role": "Chantre", "principal": True},
            )

    def _seed_roles(self, lib):
        return {r: self._get_or_create(Role, libelle=r)[0] for r in lib}

    def _seed_permissions(self, d):
        return {
            c: self._get_or_create(
                Permission, code=c, defaults={"description": f"Accès {c}"}
            )[0]
            for codes in d.values()
            for c in codes
        }

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

    def _seed_voix(self):
        for v in VOIX_DATA:
            self._get_or_create(Voix, code=v["code"], defaults={"nom": v["nom"]})

    def _seed_activites(self, cid):
        return {
            a["type"]: self._get_or_create(
                Activite,
                type=a["type"],
                campus_id=cid,
                defaults={
                    "dateDebut": datetime.now(),
                    "dateFin": datetime.now() + timedelta(hours=2),
                    "lieu": a["lieu"],
                },
            )[0]
            for a in ACTIVITES_DATA
        }

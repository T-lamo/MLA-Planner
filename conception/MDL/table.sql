-- -------------------------
-- Tables de référence (Enums)
-- -------------------------

CREATE TABLE Voix (
    code VARCHAR(20) PRIMARY KEY
);

CREATE TABLE Instrument (
    code VARCHAR(20) PRIMARY KEY
);

CREATE TABLE StatutPlanning (
    code VARCHAR(20) PRIMARY KEY
);

CREATE TABLE TypeResponsabilite (
    code VARCHAR(50) PRIMARY KEY
);

-- -------------------------
-- Tables principales
-- -------------------------

CREATE TABLE OrganisationICC (
    id CHAR(36) PRIMARY KEY,
    nom VARCHAR(255) NOT NULL,
    dateCreation DATE NOT NULL
);

CREATE TABLE Pays (
    id CHAR(36) PRIMARY KEY,
    nom VARCHAR(255) NOT NULL,
    code VARCHAR(10) NOT NULL,
    organisation_id CHAR(36) NOT NULL,
    FOREIGN KEY (organisation_id) REFERENCES OrganisationICC(id)
);

CREATE TABLE Campus (
    id CHAR(36) PRIMARY KEY,
    nom VARCHAR(255) NOT NULL,
    ville VARCHAR(255) NOT NULL,
    timezone VARCHAR(50) NOT NULL,
    pays_id CHAR(36) NOT NULL,
    FOREIGN KEY (pays_id) REFERENCES Pays(id)
);

CREATE TABLE Ministere (
    id CHAR(36) PRIMARY KEY,
    nom VARCHAR(255) NOT NULL,
    dateCreation DATE NOT NULL,
    actif BOOLEAN NOT NULL DEFAULT TRUE,
    campus_id CHAR(36) NOT NULL,
    FOREIGN KEY (campus_id) REFERENCES Campus(id)
);

CREATE TABLE Pole (
    id CHAR(36) PRIMARY KEY,
    nom VARCHAR(255) NOT NULL,
    description TEXT,
    ministere_id CHAR(36) NOT NULL,
    FOREIGN KEY (ministere_id) REFERENCES Ministere(id)
);

CREATE TABLE Membre (
    id CHAR(36) PRIMARY KEY,
    nom VARCHAR(255) NOT NULL,
    prenom VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    telephone VARCHAR(50),
    date_inscription DATE,
    actif BOOLEAN NOT NULL DEFAULT TRUE,
    ministere_id CHAR(36) NOT NULL,
    pole_id CHAR(36) NOT NULL,
    FOREIGN KEY (ministere_id) REFERENCES Ministere(id),
    FOREIGN KEY (pole_id) REFERENCES Pole(id)
);

CREATE TABLE Chantre (
    id CHAR(36) PRIMARY KEY,
    date_integration DATE,
    niveau VARCHAR(50),
    membre_id CHAR(36) NOT NULL,
    FOREIGN KEY (membre_id) REFERENCES Membre(id)
);

CREATE TABLE Choriste (
    id CHAR(36) PRIMARY KEY,
    voix_code VARCHAR(20) NOT NULL,
    secondaireVoix VARCHAR(50),
    chantre_id CHAR(36) NOT NULL,
    FOREIGN KEY (voix_code) REFERENCES Voix(code),
    FOREIGN KEY (chantre_id) REFERENCES Chantre(id)
);

CREATE TABLE Musicien (
    id CHAR(36) PRIMARY KEY,
    instrument_code VARCHAR(20) NOT NULL,
    instrumentPrincipal VARCHAR(50),
    chantre_id CHAR(36) NOT NULL,
    FOREIGN KEY (instrument_code) REFERENCES Instrument(code),
    FOREIGN KEY (chantre_id) REFERENCES Chantre(id)
);

CREATE TABLE Equipe (
    id CHAR(36) PRIMARY KEY,
    nom VARCHAR(255) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    ministere_id CHAR(36) NOT NULL,
    FOREIGN KEY (ministere_id) REFERENCES Ministere(id)
);

CREATE TABLE Equipe_Membre (
    equipe_id CHAR(36) NOT NULL,
    membre_id CHAR(36) NOT NULL,
    PRIMARY KEY (equipe_id, membre_id),
    FOREIGN KEY (equipe_id) REFERENCES Equipe(id),
    FOREIGN KEY (membre_id) REFERENCES Membre(id)
);

CREATE TABLE Activite (
    id CHAR(36) PRIMARY KEY,
    type VARCHAR(100),
    dateDebut DATETIME,
    dateFin DATETIME,
    lieu VARCHAR(255),
    description TEXT,
    campus_id CHAR(36) NOT NULL,
    FOREIGN KEY (campus_id) REFERENCES Campus(id)
);

CREATE TABLE PlanningService (
    id CHAR(36) PRIMARY KEY,
    statut_code VARCHAR(20) NOT NULL,
    dateCreation DATE,
    activite_id CHAR(36) NOT NULL,
    FOREIGN KEY (statut_code) REFERENCES StatutPlanning(code),
    FOREIGN KEY (activite_id) REFERENCES Activite(id)
);

CREATE TABLE Affectation (
    id CHAR(36) PRIMARY KEY,
    role VARCHAR(50),
    voix_code VARCHAR(20),
    instrument_code VARCHAR(20),
    principal BOOLEAN DEFAULT FALSE,
    presenceConfirmee BOOLEAN DEFAULT FALSE,
    planning_id CHAR(36) NOT NULL,
    chantre_id CHAR(36) NOT NULL,
    FOREIGN KEY (voix_code) REFERENCES Voix(code),
    FOREIGN KEY (instrument_code) REFERENCES Instrument(code),
    FOREIGN KEY (planning_id) REFERENCES PlanningService(id),
    FOREIGN KEY (chantre_id) REFERENCES Chantre(id)
);

CREATE TABLE Indisponibilite (
    id CHAR(36) PRIMARY KEY,
    dateDebut DATE,
    dateFin DATE,
    motif TEXT,
    validee BOOLEAN DEFAULT FALSE,
    chantre_id CHAR(36) NOT NULL,
    FOREIGN KEY (chantre_id) REFERENCES Chantre(id)
);

CREATE TABLE Responsabilite (
    id CHAR(36) PRIMARY KEY,
    type_code VARCHAR(50) NOT NULL,
    dateDebut DATE,
    dateFin DATE,
    actif BOOLEAN DEFAULT TRUE,
    membre_id CHAR(36) NOT NULL,
    ministere_id CHAR(36),
    pole_id CHAR(36),
    activite_id CHAR(36),
    FOREIGN KEY (type_code) REFERENCES TypeResponsabilite(code),
    FOREIGN KEY (membre_id) REFERENCES Membre(id),
    FOREIGN KEY (ministere_id) REFERENCES Ministere(id),
    FOREIGN KEY (pole_id) REFERENCES Pole(id),
    FOREIGN KEY (activite_id) REFERENCES Activite(id)
);

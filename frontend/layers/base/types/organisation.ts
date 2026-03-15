export interface OrganisationRead {
  id: string
  nom: string
  date_creation: string
  pays: { id: string; nom: string; code: string; organisation_id: string; campus: unknown[] }[]
}

export interface OrganisationCreate {
  nom: string
  date_creation: string
}

export interface OrganisationUpdate {
  nom?: string
  dateCreation?: string
}

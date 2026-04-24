export interface OrganisationRead {
  id: string
  nom: string
  date_creation: string
  parent_id: string | null
  children: OrganisationRead[]
}

export interface OrganisationCreate {
  nom: string
  date_creation: string
  parent_id?: string | null
}

export interface OrganisationUpdate {
  nom?: string
  date_creation?: string
  parent_id?: string | null
}

export interface PaysRead {
  id: string
  nom: string
  code: string
  organisation_id: string
  campus: unknown[]
}

export interface PaysCreate {
  nom: string
  code: string
  organisation_id: string
}

export interface PaysUpdate {
  nom?: string
  code?: string
  organisation_id?: string
}

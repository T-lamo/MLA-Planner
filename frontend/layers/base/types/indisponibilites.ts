// types/indisponibilites.ts

export interface IndisponibiliteCreate {
  date_debut: string // YYYY-MM-DD
  date_fin: string
  motif?: string | null
  ministere_id?: string | null
  membre_id: string
}

export interface IndisponibiliteRead {
  id: string
  membre_id: string
  ministere_id: string | null
  date_debut: string | null
  date_fin: string | null
  motif: string | null
  validee: boolean
}

export interface IndisponibiliteReadFull extends IndisponibiliteRead {
  membre_nom: string
  membre_prenom: string
  ministere_libelle: string | null
}

export interface IndisponibiliteUpdate {
  date_debut?: string
  date_fin?: string
  motif?: string | null
  ministere_id?: string | null
}

export interface IndisponibiliteFilters {
  ministere_id?: string
  date_debut?: string
  date_fin?: string
  validee_only?: boolean
}

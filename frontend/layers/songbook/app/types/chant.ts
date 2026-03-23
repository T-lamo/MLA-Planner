// ---- Requêtes ----

export interface ChantCategorieCreate {
  code: string
  libelle: string
  ordre?: number
  description?: string
}

export interface ChantCategorieUpdate {
  libelle?: string
  ordre?: number
  description?: string
}

export interface ChantCreate {
  titre: string
  artiste?: string
  campus_id: string
  categorie_code?: string
  youtube_url?: string | null
}

export interface ChantUpdate {
  titre?: string
  artiste?: string
  categorie_code?: string
  youtube_url?: string | null
}

export interface ChantContenuCreate {
  tonalite: string
  paroles_chords: string
}

export interface ChantContenuUpdate {
  tonalite?: string
  paroles_chords?: string
  version: number
}

export interface ChantTransposeRequest {
  semitones: number
}

// ---- Réponses ----

export interface ChantCategorieRead {
  code: string
  libelle: string
  ordre: number
  description?: string
}

export interface ChantRead {
  id: string
  titre: string
  artiste?: string
  campus_id: string
  categorie_code?: string
  actif: boolean
  date_creation: string
  youtube_url?: string | null
}

export interface ChantContenuRead {
  id: string
  chant_id: string
  tonalite: string
  paroles_chords: string
  version: number
  date_modification: string
}

export interface ChantReadFull extends ChantRead {
  contenu?: ChantContenuRead
  categorie?: ChantCategorieRead
}

export interface ChantTransposeResponse {
  tonalite_originale: string
  tonalite_transposee: string
  paroles_chords: string
}

export interface ChantListParams {
  campus_id?: string
  categorie_code?: string
  artiste?: string
  q?: string
  limit?: number
  offset?: number
}

export interface PaginatedChants {
  total: number
  limit: number
  offset: number
  data: ChantRead[]
}

export interface RoleCompetenceRead {
  code: string
  libelle: string
  categorie_code: string
  description?: string
}

export interface RolesByCategoryItem {
  categorie_code: string
  categorie_libelle: string
  roles: RoleCompetenceRead[]
}

export interface RolesByCategoryResponse {
  data: RolesByCategoryItem[]
}

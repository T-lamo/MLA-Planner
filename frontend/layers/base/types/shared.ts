export type UUID = string
export type ISO8601String = string

export enum RoleNiveau {
  DEBUTANT = 'DEBUTANT',
  INTERMEDIAIRE = 'INTERMEDIAIRE',
  EXPERT = 'EXPERT',
}

export interface PaginatedResponse<T> {
  total: number
  limit: number
  offset: number
  data: T[]
}

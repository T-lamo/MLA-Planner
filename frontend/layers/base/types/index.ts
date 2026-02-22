export interface User {
  id: string
  email: string
  role: 'admin' | 'user'
}

export interface Shift {
  id: string
  userId: string
  start: Date
  end: Date
  title: string
}

export type ApiError = {
  message: string
  statusCode: number
}

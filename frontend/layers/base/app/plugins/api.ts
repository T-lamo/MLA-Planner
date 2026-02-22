import { AuthRepository } from '~~/layers/auth/app/repositories/AuthRepository'

export default defineNuxtPlugin(() => {
  // Instances uniques (Singleton)
  const apiContext = {
    auth: new AuthRepository(),
  }

  return {
    provide: {
      api: apiContext,
    },
  }
})

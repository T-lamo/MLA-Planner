import { ref, readonly, type Ref } from 'vue'

export interface Loader {
  isLoading: Readonly<Ref<boolean>>
  startLoading: () => void
  stopLoading: () => void
  withLoader: <T>(fn: () => Promise<T>) => Promise<T>
}

// Singleton module-level : partagé dans toute l'app
const globalIsLoading = ref(false)

function createLoader(isLoading: Ref<boolean>): Loader {
  const startLoading = () => {
    isLoading.value = true
  }

  const stopLoading = () => {
    isLoading.value = false
  }

  const withLoader = async <T>(fn: () => Promise<T>): Promise<T> => {
    startLoading()
    try {
      return await fn()
    } finally {
      stopLoading()
    }
  }

  return {
    isLoading: readonly(isLoading),
    startLoading,
    stopLoading,
    withLoader,
  }
}

/** Loader global partagé dans toute l'application. */
export function useGlobalLoader(): Loader {
  return createLoader(globalIsLoading)
}

/** Loader local isolé au composant appelant. */
export function useLoader(): Loader {
  const localIsLoading = ref(false)
  return createLoader(localIsLoading)
}

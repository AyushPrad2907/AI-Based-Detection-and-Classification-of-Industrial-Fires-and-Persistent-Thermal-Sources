import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api'
import type { HealthStatus } from '@/types'

/**
 * Hook to check API health status.
 */
export function useApiHealth() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let isMounted = true
    const checkHealth = async () => {
      try {
        setLoading(true)
        const response = await apiClient.get<HealthStatus>('/health/')
        if (isMounted) {
          setHealth(response.data)
          setError(null)
        }
      } catch (err: unknown) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Backend offline')
          setHealth(null)
        }
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    checkHealth()
    return () => {
      isMounted = false
    }
  }, [])

  return { health, loading, error }
}

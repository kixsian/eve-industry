import { useState, useEffect, useCallback } from 'react'
import { authApi, characterApi, AuthStatus } from '../api/client'

interface AuthState {
  status: AuthStatus
  wallet: number | null
  loading: boolean
}

export function useAuth() {
  const [state, setState] = useState<AuthState>({
    status: { authenticated: false },
    wallet: null,
    loading: true,
  })

  const refresh = useCallback(async () => {
    try {
      const { data: status } = await authApi.status()
      let wallet: number | null = null
      if (status.authenticated) {
        try {
          const { data } = await characterApi.wallet()
          wallet = data.balance
        } catch {
          // wallet fetch failing shouldn't break auth
        }
      }
      setState({ status, wallet, loading: false })
    } catch {
      setState(s => ({ ...s, loading: false }))
    }
  }, [])

  useEffect(() => {
    refresh()
    // Handle ?logged_in=true redirect back from SSO
    const params = new URLSearchParams(window.location.search)
    if (params.get('logged_in') === 'true') {
      window.history.replaceState({}, '', window.location.pathname)
    }
  }, [refresh])

  const logout = useCallback(async () => {
    await authApi.logout()
    setState({ status: { authenticated: false }, wallet: null, loading: false })
  }, [])

  return { ...state, refresh, logout }
}

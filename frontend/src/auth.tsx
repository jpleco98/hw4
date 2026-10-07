import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import * as api from './api'

interface AuthState {
  user: api.User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (input: api.SignupInput) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthState | null>(null)

// The session itself lives in an HttpOnly cookie set by the backend; we only keep the public user profile here.
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<api.User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .getMe()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  const value: AuthState = {
    user,
    loading,
    login: async (email, password) => setUser(await api.login(email, password)),
    signup: async (input) => setUser(await api.signup(input)),
    logout: async () => {
      await api.logout().catch(() => undefined)
      setUser(null)
    },
  }
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}

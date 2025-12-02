import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

const API_BASE = 'http://localhost:8051';

interface AuthContextType {
  isAuthenticated: boolean;
  isAuthEnabled: boolean;
  isLoading: boolean;
  user: { email: string } | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isAuthEnabled, setIsAuthEnabled] = useState(true);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<{ email: string } | null>(null);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      // Check if auth is enabled
      const statusRes = await fetch(`${API_BASE}/api/auth/status`);
      if (statusRes.ok) {
        const statusData = await statusRes.json();
        setIsAuthEnabled(statusData.auth_enabled);

        if (!statusData.auth_enabled) {
          setIsAuthenticated(true);
          setIsLoading(false);
          return;
        }
      }

      // Check if user is already logged in
      const token = localStorage.getItem('auth_token');
      if (token) {
        const meRes = await fetch(`${API_BASE}/api/auth/me`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (meRes.ok) {
          const userData = await meRes.json();
          setUser(userData);
          setIsAuthenticated(true);
        } else {
          localStorage.removeItem('auth_token');
        }
      }
    } catch (error) {
      // If we can't reach the server, assume auth is disabled for local dev
      console.warn('Could not check auth status:', error);
      setIsAuthEnabled(false);
      setIsAuthenticated(true);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.detail || 'Login failed');
    }

    const data = await res.json();
    localStorage.setItem('auth_token', data.access_token);
    setUser({ email });
    setIsAuthenticated(true);
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    setUser(null);
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, isAuthEnabled, isLoading, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

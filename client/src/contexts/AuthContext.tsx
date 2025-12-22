import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import AuthService, { User } from '../api/services/AuthService';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for existing auth on mount
    const initAuth = async () => {
      if (AuthService.isAuthenticated()) {
        try {
          const currentUser = await AuthService.getCurrentUser();
          setUser(currentUser);
        } catch {
          // Token invalid, clear it
          AuthService.logout();
        }
      }
      setIsLoading(false);
    };
    initAuth();
  }, []);

  const login = async (username: string, password: string) => {
    const response = await AuthService.login(username, password);
    setUser(response.user);
  };

  const logout = () => {
    AuthService.logout();
    setUser(null);
  };

  const refreshUser = async () => {
    if (AuthService.isAuthenticated()) {
      const currentUser = await AuthService.getCurrentUser();
      setUser(currentUser);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        refreshUser,
      }}
    >
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

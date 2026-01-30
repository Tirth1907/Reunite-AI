import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { login as apiLogin, signup as apiSignup, type LoginResponse } from '@/app/services/api';

interface User {
  id: string;
  name: string;
  email: string;
  phone: string;
  role: 'family' | 'volunteer' | 'ngo' | 'police' | 'admin';
  avatar?: string;
  area?: string;
  city?: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (userData: Partial<User> & { password: string }) => Promise<void>;
  logout: () => void;
  updateUser: (userData: Partial<User>) => void;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  // Start with isHydrating true to prevent redirect during initial load
  const [isHydrating, setIsHydrating] = useState(true);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Hydrate auth state from localStorage on mount
  useEffect(() => {
    const storedUser = localStorage.getItem('reunite_user');
    const storedToken = localStorage.getItem('reunite_token');
    if (storedUser && storedToken) {
      try {
        setUser(JSON.parse(storedUser));
      } catch {
        localStorage.removeItem('reunite_user');
        localStorage.removeItem('reunite_token');
      }
    }
    setIsHydrating(false);
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);

    try {
      // Use email as username for API call
      const response: LoginResponse = await apiLogin(email, password);

      const userData: User = {
        id: response.user.id,
        name: response.user.name,
        email: response.user.email,
        phone: response.user.phone,
        role: response.user.role as User['role'],
        area: response.user.area,
        city: response.user.city,
      };

      // Store token and user data
      localStorage.setItem('reunite_token', response.access_token);
      localStorage.setItem('reunite_user', JSON.stringify(userData));

      setUser(userData);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Login failed';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const signup = async (userData: Partial<User> & { password: string }) => {
    setIsLoading(true);
    setError(null);

    try {
      const response: LoginResponse = await apiSignup({
        name: userData.name || '',
        email: userData.email || '',
        phone: userData.phone || '',
        password: userData.password,
        role: userData.role,
      });

      const newUser: User = {
        id: response.user.id,
        name: response.user.name,
        email: response.user.email,
        phone: response.user.phone,
        role: response.user.role as User['role'],
      };

      // Store token and user data
      localStorage.setItem('reunite_token', response.access_token);
      localStorage.setItem('reunite_user', JSON.stringify(newUser));

      setUser(newUser);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Signup failed';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('reunite_user');
    localStorage.removeItem('reunite_token');
  };

  const updateUser = (userData: Partial<User>) => {
    if (user) {
      const updatedUser = { ...user, ...userData };
      setUser(updatedUser);
      localStorage.setItem('reunite_user', JSON.stringify(updatedUser));
    }
  };

  const clearError = () => setError(null);

  return (
    <AuthContext.Provider value={{
      user,
      isAuthenticated: !!user,
      isLoading: isLoading || isHydrating, // Include hydrating state in loading
      error,
      login,
      signup,
      logout,
      updateUser,
      clearError,
    }}>
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

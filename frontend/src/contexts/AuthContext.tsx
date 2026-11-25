import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../services/api';

export interface User {
  id: string;
  organization_id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  phone?: string;
  timezone: string;
}

interface AuthContextType {
  user: User | null;
  organization: Organization | null;
  isLoading: boolean;
  login: (credentials: any) => Promise<void>;
  register: (data: any) => Promise<void>;
  logout: () => void;
  refreshOrg: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchCurrentUser = async () => {
    const token = localStorage.getItem('voicedesk_token');
    if (!token) {
      setIsLoading(false);
      return;
    }
    try {
      const data = await api.getMe();
      setUser(data.user);
      setOrganization(data.organization);
    } catch (err) {
      localStorage.removeItem('voicedesk_token');
      localStorage.removeItem('voicedesk_refresh_token');
      setUser(null);
      setOrganization(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCurrentUser();
  }, []);

  const login = async (credentials: any) => {
    setIsLoading(true);
    try {
      const resp = await api.login(credentials);
      localStorage.setItem('voicedesk_token', resp.token.access_token);
      localStorage.setItem('voicedesk_refresh_token', resp.token.refresh_token);
      setUser(resp.user);
      setOrganization(resp.organization);
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (data: any) => {
    setIsLoading(true);
    try {
      const resp = await api.register(data);
      localStorage.setItem('voicedesk_token', resp.token.access_token);
      localStorage.setItem('voicedesk_refresh_token', resp.token.refresh_token);
      setUser(resp.user);
      setOrganization(resp.organization);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('voicedesk_token');
    localStorage.removeItem('voicedesk_refresh_token');
    setUser(null);
    setOrganization(null);
  };

  const refreshOrg = async () => {
    await fetchCurrentUser();
  };

  return (
    <AuthContext.Provider value={{ user, organization, isLoading, login, register, logout, refreshOrg }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

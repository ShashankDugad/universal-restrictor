import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface AuthContextType {
  isAuthenticated: boolean;
  apiKey: string;
  tenant: string;
  tier: string;
  login: (apiKey: string) => Promise<boolean>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [tenant, setTenant] = useState('');
  const [tier, setTier] = useState('');

  useEffect(() => {
    const savedKey = localStorage.getItem('apiKey');
    const savedTenant = localStorage.getItem('tenant');
    const savedTier = localStorage.getItem('tier');
    if (savedKey) {
      setApiKey(savedKey);
      setTenant(savedTenant || 'local-dev');
      setTier(savedTier || 'free');
      setIsAuthenticated(true);
    }
  }, []);

  const login = async (key: string): Promise<boolean> => {
    try {
      const response = await fetch('http://localhost:8000/health', {
        headers: { 'X-API-Key': key }
      });
      if (response.ok) {
        localStorage.setItem('apiKey', key);
        localStorage.setItem('tenant', 'local-dev');
        localStorage.setItem('tier', 'pro');
        setApiKey(key);
        setTenant('local-dev');
        setTier('pro');
        setIsAuthenticated(true);
        return true;
      }
      return false;
    } catch {
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem('apiKey');
    localStorage.removeItem('tenant');
    localStorage.removeItem('tier');
    setApiKey('');
    setTenant('');
    setTier('');
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, apiKey, tenant, tier, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};

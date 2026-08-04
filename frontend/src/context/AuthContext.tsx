'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { User } from '../lib/types';
import { api } from '../lib/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, full_name: string) => Promise<void>;
  loginWithGoogleMock: () => Promise<void>;
  loginWithToken: (jwtToken: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchUser = async () => {
    try {
      const storedToken = localStorage.getItem('token');
      if (!storedToken) {
        setUser(null);
        setToken(null);
        setLoading(false);
        return;
      }
      setToken(storedToken);
      const userData = await api.getMe();
      setUser(userData);
    } catch {
      localStorage.removeItem('token');
      setUser(null);
      setToken(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUser();
  }, []);

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      const res = await api.login(email, password);
      setUser(res.user);
      setToken(res.access_token);
    } finally {
      setLoading(false);
    }
  };

  const register = async (email: string, password: string, full_name: string) => {
    setLoading(true);
    try {
      const res = await api.register(email, password, full_name);
      setUser(res.user);
      setToken(res.access_token);
    } finally {
      setLoading(false);
    }
  };

  const loginWithGoogleMock = async () => {
    setLoading(true);
    try {
      const res = await api.loginWithGoogleMock();
      setUser(res.user);
      setToken(res.access_token);
    } finally {
      setLoading(false);
    }
  };

  const loginWithToken = async (jwtToken: string) => {
    setLoading(true);
    try {
      localStorage.setItem('token', jwtToken);
      setToken(jwtToken);
      const userData = await api.getMe();
      setUser(userData);
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
    setToken(null);
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        register,
        loginWithGoogleMock,
        loginWithToken,
        logout,
      }}
    >
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

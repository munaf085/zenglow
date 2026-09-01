"use client";

import { createContext, useContext, useEffect, useState, useCallback } from "react";
import type { User } from "@zenglow/types";
import { api, clearTokens, setTokens } from "@/lib/api";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    const token = localStorage.getItem("zenglow_access_token");
    if (!token) { setUser(null); setIsLoading(false); return; }
    try {
      const me = await api.get<User>("/auth/me");
      setUser(me);
    } catch {
      setUser(null);
      clearTokens();
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => { refreshUser(); }, [refreshUser]);

  // Listen for unauthorized events from the api client
  useEffect(() => {
    const handler = () => { setUser(null); };
    window.addEventListener("zenglow:unauthorized", handler);
    return () => window.removeEventListener("zenglow:unauthorized", handler);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const tokens = await api.post<{ access_token: string; refresh_token: string }>("/auth/login", { email, password });
    setTokens(tokens.access_token, tokens.refresh_token);
    await refreshUser();
  }, [refreshUser]);

  const logout = useCallback(async () => {
    const refresh = localStorage.getItem("zenglow_refresh_token");
    try {
      if (refresh) await api.post("/auth/logout", { refresh_token: refresh });
    } finally {
      clearTokens();
      setUser(null);
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, isAuthenticated: !!user, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

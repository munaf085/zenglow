"use client";
import { createContext, useContext, useEffect, useState, useCallback } from "react";
import type { User, Business } from "@zenglow/types";
import { api, clearTokens, setTokens } from "@/lib/api";

interface AuthCtx {
  user: User | null;
  business: Business | null;
  businesses: Business[];
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  selectBusiness: (b: Business) => void;
  refreshUser: () => Promise<void>;
}

const Ctx = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [business, setBusiness] = useState<Business | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    const token = typeof window !== "undefined" ? localStorage.getItem("biz_access_token") : null;
    if (!token) {
      setUser(null);
      setBusiness(null);
      setBusinesses([]);
      setIsLoading(false);
      return;
    }
    try {
      const [me, res] = await Promise.all([
        api.get<User>("/auth/me"),
        api.get<{ items: Business[] }>("/businesses"),
      ]);
      setUser(me);
      const bizList = res?.items ?? [];
      setBusinesses(bizList);
      if (bizList.length > 0) {
        setBusiness((prev) => prev ?? bizList[0]);
      }
    } catch {
      setUser(null);
      setBusiness(null);
      setBusinesses([]);
      clearTokens();
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = useCallback(async (email: string, password: string) => {
    const tokens = await api.post<{ access_token: string; refresh_token: string }>("/auth/login", { email, password });
    setTokens(tokens.access_token, tokens.refresh_token);
    await refreshUser();
  }, [refreshUser]);

  const logout = useCallback(async () => {
    const refresh = localStorage.getItem("biz_refresh_token");
    try { if (refresh) await api.post("/auth/logout", { refresh_token: refresh }); } finally {
      clearTokens(); setUser(null); setBusiness(null); setBusinesses([]);
    }
  }, []);

  return (
    <Ctx.Provider value={{ user, business, businesses, isLoading, isAuthenticated: !!user, login, logout, selectBusiness: setBusiness, refreshUser }}>
      {children}
    </Ctx.Provider>
  );
}

export function useAuth(): AuthCtx {
  const c = useContext(Ctx);
  if (!c) throw new Error("useAuth must be within AuthProvider");
  return c;
}

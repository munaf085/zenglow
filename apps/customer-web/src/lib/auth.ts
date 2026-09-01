import { api, setTokens, clearTokens } from "./api";
import type { User, TokenResponse } from "@zenglow/types";

export async function login(email: string, password: string): Promise<{ user: User; tokens: TokenResponse }> {
  const tokens = await api.post<TokenResponse>("/auth/login", { email, password });
  setTokens(tokens.access_token, tokens.refresh_token);
  const user = await api.get<User>("/auth/me");
  return { user, tokens };
}

export async function register(data: {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone?: string;
}): Promise<User> {
  return api.post<User>("/auth/register", data);
}

export async function logout(refreshToken: string): Promise<void> {
  try {
    await api.post("/auth/logout", { refresh_token: refreshToken });
  } finally {
    clearTokens();
  }
}

export function isAuthenticated(): boolean {
  if (typeof window === "undefined") return false;
  return !!localStorage.getItem("zenglow_access_token");
}

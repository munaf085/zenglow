/**
 * API helper for Customer Web.
 */
const BASE = "/api/v1";

type Method = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("zenglow_access_token");
}

export function setTokens(access: string, refresh: string) {
  localStorage.setItem("zenglow_access_token", access);
  localStorage.setItem("zenglow_refresh_token", refresh);
}

export function clearTokens() {
  localStorage.removeItem("zenglow_access_token");
  localStorage.removeItem("zenglow_refresh_token");
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string
  ) {
    super(message);
  }
}

async function request<T>(path: string, method: Method, body?: unknown, skipAuth = false): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const token = getToken();
  if (token && !skipAuth) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body != null ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401 && !skipAuth) {
    // Try refresh
    const refresh = localStorage.getItem("zenglow_refresh_token");
    if (refresh) {
      const rRes = await fetch(`${BASE}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refresh }),
      });
      if (rRes.ok) {
        const tokens = await rRes.json();
        setTokens(tokens.access_token, tokens.refresh_token);
        return request<T>(path, method, body, skipAuth);
      }
    }
    clearTokens();
    window.location.href = "/login";
    throw new ApiError(401, "UNAUTHORIZED", "Session expired");
  }

  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    let code = "ERROR";
    try {
      const err = await res.json();
      msg = err?.error?.message ?? msg;
      code = err?.error?.code ?? code;
    } catch { /* ignore */ }
    throw new ApiError(res.status, code, msg);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  get: <T>(path: string) => request<T>(path, "GET"),
  post: <T>(path: string, body?: unknown) => request<T>(path, "POST", body),
  patch: <T>(path: string, body?: unknown) => request<T>(path, "PATCH", body),
  delete: <T>(path: string) => request<T>(path, "DELETE"),
  publicGet: <T>(path: string) => request<T>(path, "GET", undefined, true),
};

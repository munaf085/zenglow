const BASE = "/api/v1";

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string) {
    super(message);
  }
}

export function getToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("biz_access_token");
}

export function setTokens(access: string, refresh: string) {
  localStorage.setItem("biz_access_token", access);
  localStorage.setItem("biz_refresh_token", refresh);
}

export function clearTokens() {
  localStorage.removeItem("biz_access_token");
  localStorage.removeItem("biz_refresh_token");
}

async function request<T>(path: string, method: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body != null ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401) {
    const refresh = localStorage.getItem("biz_refresh_token");
    if (refresh) {
      const rr = await fetch(`${BASE}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refresh }),
      });
      if (rr.ok) {
        const t = await rr.json();
        setTokens(t.access_token, t.refresh_token);
        return request<T>(path, method, body);
      }
    }
    clearTokens();
    if (typeof window !== "undefined") window.location.href = "/login";
    throw new ApiError(401, "UNAUTHORIZED", "Session expired");
  }

  if (!res.ok) {
    let msg = `HTTP ${res.status}`, code = "ERROR";
    try { const e = await res.json(); msg = e?.error?.message ?? msg; code = e?.error?.code ?? code; } catch { /* ignore */ }
    throw new ApiError(res.status, code, msg);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  get: <T>(path: string) => request<T>(path, "GET"),
  post: <T>(path: string, body?: unknown) => request<T>(path, "POST", body),
  patch: <T>(path: string, body?: unknown) => request<T>(path, "PATCH", body),
  put: <T>(path: string, body?: unknown) => request<T>(path, "PUT", body),
  delete: <T>(path: string) => request<T>(path, "DELETE"),
};

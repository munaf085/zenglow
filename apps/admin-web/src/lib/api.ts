const BASE = "/api/v1";

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string) { super(message); }
}

export function setTokens(a: string, r: string) {
  localStorage.setItem("admin_access_token", a);
  localStorage.setItem("admin_refresh_token", r);
}
export function clearTokens() {
  localStorage.removeItem("admin_access_token");
  localStorage.removeItem("admin_refresh_token");
}

async function req<T>(path: string, method: string, body?: unknown): Promise<T> {
  const h: Record<string, string> = { "Content-Type": "application/json" };
  const t = typeof window !== "undefined" ? localStorage.getItem("admin_access_token") : null;
  if (t) h["Authorization"] = `Bearer ${t}`;
  const res = await fetch(`${BASE}${path}`, { method, headers: h, body: body != null ? JSON.stringify(body) : undefined });
  if (res.status === 401) { clearTokens(); if (typeof window !== "undefined") window.location.href = "/login"; throw new ApiError(401, "UNAUTHORIZED", "Session expired"); }
  if (!res.ok) {
    let msg = `HTTP ${res.status}`, code = "ERROR";
    try { const e = await res.json(); msg = e?.error?.message ?? msg; code = e?.error?.code ?? code; } catch { /* ignore */ }
    throw new ApiError(res.status, code, msg);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  get: <T>(p: string) => req<T>(p, "GET"),
  post: <T>(p: string, b?: unknown) => req<T>(p, "POST", b),
  patch: <T>(p: string, b?: unknown) => req<T>(p, "PATCH", b),
};

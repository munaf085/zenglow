/**
 * Shared API client for all Zenglow frontend applications.
 * Handles auth tokens, refresh rotation, and consistent error handling.
 */
import { API_BASE_URL } from "./index";

type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

interface RequestOptions {
  method?: HttpMethod;
  body?: unknown;
  headers?: Record<string, string>;
  noAuth?: boolean;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details?: Record<string, unknown>
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("zenglow_access_token");
}

function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("zenglow_refresh_token");
}

export function setTokens(accessToken: string, refreshToken: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem("zenglow_access_token", accessToken);
  localStorage.setItem("zenglow_refresh_token", refreshToken);
}

export function clearTokens(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem("zenglow_access_token");
  localStorage.removeItem("zenglow_refresh_token");
}

let isRefreshing = false;
let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return null;

  try {
    const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!res.ok) {
      clearTokens();
      return null;
    }
    const data = await res.json();
    setTokens(data.access_token, data.refresh_token);
    return data.access_token;
  } catch {
    clearTokens();
    return null;
  }
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const { method = "GET", body, headers = {}, noAuth = false } = options;

  const buildHeaders = (token?: string | null): Headers => {
    const h = new Headers({
      "Content-Type": "application/json",
      ...headers,
    });
    if (!noAuth && token) {
      h.set("Authorization", `Bearer ${token}`);
    }
    return h;
  };

  const doRequest = async (token?: string | null): Promise<Response> => {
    return fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: buildHeaders(token),
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  };

  let token = getAccessToken();
  let res = await doRequest(token);

  // Attempt token refresh on 401
  if (res.status === 401 && !noAuth) {
    if (!isRefreshing) {
      isRefreshing = true;
      refreshPromise = refreshAccessToken().finally(() => {
        isRefreshing = false;
        refreshPromise = null;
      });
    }
    token = await refreshPromise;
    if (token) {
      res = await doRequest(token);
    } else {
      // Redirect to login
      if (typeof window !== "undefined") {
        window.dispatchEvent(new CustomEvent("zenglow:unauthorized"));
      }
      throw new ApiError(401, "AUTHENTICATION_ERROR", "Session expired. Please log in again.");
    }
  }

  if (!res.ok) {
    let errorData: { error?: { code: string; message: string; details?: Record<string, unknown> } } = {};
    try {
      errorData = await res.json();
    } catch {
      // ignore
    }
    throw new ApiError(
      res.status,
      errorData?.error?.code ?? "UNKNOWN_ERROR",
      errorData?.error?.message ?? `Request failed with status ${res.status}`,
      errorData?.error?.details
    );
  }

  // 204 No Content
  if (res.status === 204) return undefined as T;

  return res.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string, options?: Omit<RequestOptions, "method" | "body">) =>
    apiRequest<T>(path, { ...options, method: "GET" }),
  post: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, "method">) =>
    apiRequest<T>(path, { ...options, method: "POST", body }),
  patch: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, "method">) =>
    apiRequest<T>(path, { ...options, method: "PATCH", body }),
  put: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, "method">) =>
    apiRequest<T>(path, { ...options, method: "PUT", body }),
  delete: <T>(path: string, options?: Omit<RequestOptions, "method" | "body">) =>
    apiRequest<T>(path, { ...options, method: "DELETE" }),
};

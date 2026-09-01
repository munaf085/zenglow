import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { ApiError, setTokens, clearTokens } from "@/lib/api";

// ── Mock localStorage ─────────────────────────────────────────────────────────
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => { store[key] = value; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; },
  };
})();

Object.defineProperty(globalThis, "localStorage", { value: localStorageMock });

describe("setTokens / clearTokens", () => {
  beforeEach(() => localStorage.clear());

  it("stores access and refresh tokens", () => {
    setTokens("access123", "refresh456");
    expect(localStorage.getItem("zenglow_access_token")).toBe("access123");
    expect(localStorage.getItem("zenglow_refresh_token")).toBe("refresh456");
  });

  it("clears both tokens", () => {
    setTokens("access123", "refresh456");
    clearTokens();
    expect(localStorage.getItem("zenglow_access_token")).toBeNull();
    expect(localStorage.getItem("zenglow_refresh_token")).toBeNull();
  });
});

describe("ApiError", () => {
  it("creates error with correct properties", () => {
    const err = new ApiError(404, "NOT_FOUND", "Resource not found");
    expect(err.status).toBe(404);
    expect(err.code).toBe("NOT_FOUND");
    expect(err.message).toBe("Resource not found");
    expect(err instanceof Error).toBe(true);
  });

  it("inherits from Error", () => {
    const err = new ApiError(500, "SERVER_ERROR", "Internal error");
    expect(err instanceof Error).toBe(true);
    expect(err.name).toBe("ApiError");
  });
});

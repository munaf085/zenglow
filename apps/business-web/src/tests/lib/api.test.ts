import { describe, it, expect, beforeEach } from "vitest";
import { ApiError, setTokens, clearTokens } from "@/lib/api";

const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (k: string) => store[k] ?? null,
    setItem: (k: string, v: string) => { store[k] = v; },
    removeItem: (k: string) => { delete store[k]; },
    clear: () => { store = {}; },
  };
})();
Object.defineProperty(globalThis, "localStorage", { value: localStorageMock });

describe("setTokens / clearTokens (business-web)", () => {
  beforeEach(() => localStorage.clear());

  it("stores tokens with biz_ prefix", () => {
    setTokens("biz_access", "biz_refresh");
    expect(localStorage.getItem("biz_access_token")).toBe("biz_access");
    expect(localStorage.getItem("biz_refresh_token")).toBe("biz_refresh");
  });

  it("clears tokens", () => {
    setTokens("biz_access", "biz_refresh");
    clearTokens();
    expect(localStorage.getItem("biz_access_token")).toBeNull();
    expect(localStorage.getItem("biz_refresh_token")).toBeNull();
  });
});

describe("ApiError", () => {
  it("has correct shape", () => {
    const e = new ApiError(401, "UNAUTHORIZED", "Not authenticated");
    expect(e.status).toBe(401);
    expect(e.code).toBe("UNAUTHORIZED");
    expect(e.message).toBe("Not authenticated");
  });
});

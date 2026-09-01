import { describe, it, expect } from "vitest";
import { cn, formatCurrency, durationLabel, initials } from "@/lib/utils";

describe("cn", () => {
  it("merges class names", () => {
    expect(cn("a", "b")).toBe("a b");
  });

  it("deduplicates conflicting tailwind classes", () => {
    expect(cn("bg-red-500", "bg-blue-500")).toBe("bg-blue-500");
  });
});

describe("formatCurrency", () => {
  it("formats to INR", () => {
    const s = formatCurrency(2499);
    expect(s).toContain("2,499");
  });
});

describe("durationLabel", () => {
  it("shows minutes for sub-hour", () => {
    expect(durationLabel(30)).toBe("30 min");
  });

  it("shows hours only when exact", () => {
    expect(durationLabel(60)).toBe("1h");
  });

  it("shows hours and minutes", () => {
    expect(durationLabel(75)).toBe("1h 15min");
  });
});

describe("initials", () => {
  it("returns uppercase initials", () => {
    expect(initials("Sarah", "Johnson")).toBe("SJ");
  });

  it("handles empty strings gracefully", () => {
    expect(initials("", "")).toBe("");
  });

  it("handles single-char names", () => {
    expect(initials("A", "B")).toBe("AB");
  });
});

import { describe, it, expect } from "vitest";
import { cn, formatCurrency, formatDate, formatTime, durationLabel } from "@/lib/utils";

describe("cn", () => {
  it("merges class names", () => {
    expect(cn("foo", "bar")).toBe("foo bar");
  });

  it("removes conflicting tailwind classes", () => {
    expect(cn("p-4", "p-8")).toBe("p-8");
  });

  it("handles conditional classes", () => {
    expect(cn("base", false && "excluded", "included")).toBe("base included");
  });
});

describe("formatCurrency", () => {
  it("formats INR correctly", () => {
    const result = formatCurrency(1000);
    expect(result).toContain("1,000");
  });

  it("handles zero", () => {
    const result = formatCurrency(0);
    expect(result).toContain("0");
  });

  it("handles decimal values", () => {
    const result = formatCurrency(1499.5);
    expect(result).toContain("1,499");
  });
});

describe("durationLabel", () => {
  it("returns minutes for < 60 min", () => {
    expect(durationLabel(45)).toBe("45 min");
  });

  it("returns hours for exactly 60 min", () => {
    expect(durationLabel(60)).toBe("1h");
  });

  it("returns hours and minutes for mixed durations", () => {
    expect(durationLabel(90)).toBe("1h 30min");
  });

  it("handles 2 hours", () => {
    expect(durationLabel(120)).toBe("2h");
  });

  it("handles 2 hours 15 min", () => {
    expect(durationLabel(135)).toBe("2h 15min");
  });
});

describe("formatDate", () => {
  it("formats an ISO date string", () => {
    const result = formatDate("2024-06-15T10:00:00Z");
    expect(result).toContain("Jun");
    expect(result).toContain("15");
    expect(result).toContain("2024");
  });
});

describe("formatTime", () => {
  it("formats a time string with am/pm", () => {
    const result = formatTime("2024-06-15T10:30:00Z");
    // UTC 10:30 — exact output depends on TZ, just verify it has colon and AM/PM
    expect(result).toMatch(/\d+:\d+\s?(AM|PM)/i);
  });
});

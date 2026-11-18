import { describe, expect, it } from "vitest";
import { compactMoney, days, money, num, pct, shortMonth } from "./format";

describe("pct", () => {
  it("formats a fraction as a rounded percentage", () => {
    expect(pct(0.229)).toBe("22.9%");
  });

  it("supports a custom digit count", () => {
    expect(pct(0.229, 0)).toBe("23%");
  });

  it("returns an em dash for null/undefined/NaN", () => {
    expect(pct(null)).toBe("—");
    expect(pct(undefined)).toBe("—");
    expect(pct(NaN)).toBe("—");
  });
});

describe("num", () => {
  it("adds thousands separators", () => {
    expect(num(3000)).toBe("3,000");
  });

  it("returns an em dash for missing values", () => {
    expect(num(null)).toBe("—");
  });
});

describe("money", () => {
  it("formats a positive amount with a dollar sign and thousands separators", () => {
    expect(money(16997.07, 2)).toBe("$16,997.07");
  });

  it("puts the minus sign before the dollar sign for a negative amount", () => {
    expect(money(-500, 0)).toBe("-$500");
  });

  it("defaults to zero decimal digits", () => {
    expect(money(1929)).toBe("$1,929");
  });
});

describe("compactMoney", () => {
  it("abbreviates millions", () => {
    expect(compactMoney(4_434_353)).toBe("$4.4M");
  });

  it("abbreviates thousands", () => {
    expect(compactMoney(16_000)).toBe("$16K");
  });

  it("leaves small amounts unabbreviated", () => {
    expect(compactMoney(300)).toBe("$300");
  });

  it("preserves the sign on negative amounts", () => {
    expect(compactMoney(-24_296)).toBe("-$24K");
  });
});

describe("days", () => {
  it("appends a d suffix", () => {
    expect(days(63)).toBe("63d");
  });

  it("returns an em dash for missing values", () => {
    expect(days(null)).toBe("—");
  });
});

describe("shortMonth", () => {
  it("formats a bare YYYY-MM period string (from the Python backtest)", () => {
    expect(shortMonth("2026-01")).toBe("Jan 2026");
  });

  it("formats a full ISO timestamp (from SQL date_trunc)", () => {
    expect(shortMonth("2026-01-01T00:00:00")).toBe("Jan 2026");
  });

  it("passes through a value it can't parse as a date", () => {
    expect(shortMonth("not-a-date")).toBe("not-a-date");
  });
});

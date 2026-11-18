export function pct(x: number | null | undefined, digits = 1): string {
  if (x === null || x === undefined || Number.isNaN(x)) return "—";
  return `${(x * 100).toFixed(digits)}%`;
}

export function num(x: number | null | undefined): string {
  if (x === null || x === undefined || Number.isNaN(x)) return "—";
  return x.toLocaleString();
}

export function money(x: number | null | undefined, digits = 0): string {
  if (x === null || x === undefined || Number.isNaN(x)) return "—";
  const sign = x < 0 ? "-" : "";
  return `${sign}$${Math.abs(x).toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits })}`;
}

export function compactMoney(x: number | null | undefined): string {
  if (x === null || x === undefined || Number.isNaN(x)) return "—";
  const sign = x < 0 ? "-" : "";
  const abs = Math.abs(x);
  if (abs >= 1_000_000_000) return `${sign}$${(abs / 1_000_000_000).toFixed(1)}B`;
  if (abs >= 1_000_000) return `${sign}$${(abs / 1_000_000).toFixed(1)}M`;
  if (abs >= 1_000) return `${sign}$${(abs / 1_000).toFixed(0)}K`;
  return `${sign}$${abs.toFixed(0)}`;
}

export function days(x: number | null | undefined): string {
  if (x === null || x === undefined || Number.isNaN(x)) return "—";
  return `${x.toFixed(0)}d`;
}

/** Handles both a full ISO timestamp (from SQL date_trunc, e.g. "2026-01-01T00:00:00")
 * and a bare "YYYY-MM" period string (from the Python backtest) -- different
 * endpoints serialize "month" differently, so this normalizes both. */
export function shortMonth(period: string): string {
  const iso = /^\d{4}-\d{2}$/.test(period) ? `${period}-01` : period;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return period;
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", timeZone: "UTC" });
}

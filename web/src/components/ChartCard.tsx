import type { ReactNode } from "react";

export function ChartCard({ title, subtitle, children }: { title: string; subtitle?: string; children: ReactNode }) {
  return (
    <div
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 10,
        padding: "20px 20px 8px",
      }}
    >
      <h3 style={{ fontSize: 14, color: "var(--text-primary)" }}>{title}</h3>
      {subtitle && <p style={{ margin: "4px 0 12px", color: "var(--text-muted)", fontSize: 12 }}>{subtitle}</p>}
      <div style={{ marginTop: subtitle ? 0 : 12 }}>{children}</div>
    </div>
  );
}

type Tone = "good" | "warning" | "critical" | "neutral";

const TONE_COLOR: Record<Tone, string> = {
  good: "var(--success-text)",
  warning: "var(--status-warning)",
  critical: "var(--status-critical)",
  neutral: "var(--text-primary)",
};

export function StatTile({
  label,
  value,
  caption,
  tone = "neutral",
}: {
  label: string;
  value: string;
  caption?: string;
  tone?: Tone;
}) {
  return (
    <div
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 10,
        padding: "16px 20px",
        flex: 1,
        minWidth: 160,
      }}
    >
      <div style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
        {label}
      </div>
      <div style={{ fontSize: 28, fontWeight: 600, color: TONE_COLOR[tone], marginTop: 6 }}>{value}</div>
      {caption && <div style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 4 }}>{caption}</div>}
    </div>
  );
}

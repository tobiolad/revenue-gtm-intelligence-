import { useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../lib/api";
import { useFetch } from "../lib/useFetch";
import { ChartCard } from "../components/ChartCard";
import { ErrorBlock, Loading } from "../components/StatusBlock";
import { compactMoney, money, num, pct } from "../lib/format";

type Dimension = "industry" | "region" | "employee_band";
const DIMENSIONS: { value: Dimension; label: string }[] = [
  { value: "industry", label: "Industry" },
  { value: "region", label: "Region" },
  { value: "employee_band", label: "Company size" },
];

export default function DealsPage() {
  const lostReasons = useFetch(() => api.lostReasons(), []);
  const [dimension, setDimension] = useState<Dimension>("industry");
  const segment = useFetch(() => api.pipelineBySegment(dimension), [dimension]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <div>
        <h1 style={{ fontSize: 22 }}>Deals & Lost Reasons</h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 13, marginTop: 4 }}>
          Why deals are lost, and where the open pipeline is concentrated.
        </p>
      </div>

      <ChartCard title="Lost reason breakdown" subtitle="Closed Lost deals only.">
        {lostReasons.loading && <Loading />}
        {lostReasons.error && <ErrorBlock error={lostReasons.error} />}
        {lostReasons.data && (
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={lostReasons.data} layout="vertical" margin={{ top: 8, right: 24, left: 24, bottom: 0 }}>
              <CartesianGrid stroke="var(--gridline)" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11, fill: "var(--text-muted)" }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="lost_reason" width={100} tick={{ fontSize: 12, fill: "var(--text-secondary)" }} axisLine={false} tickLine={false} />
              <Tooltip
                formatter={(value, _n, entry) => [`${num(Number(value))} deals (${money(entry.payload.total_amount)}, ${pct(entry.payload.pct_of_losses)} of losses)`, entry.payload.lost_reason]}
                contentStyle={{ background: "var(--surface-raised)", border: "1px solid var(--border)", fontSize: 12 }}
              />
              <Bar dataKey="deal_count" fill="var(--series-8)" radius={[0, 4, 4, 0]} barSize={22} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </ChartCard>

      <ChartCard title="Open pipeline by segment">
        <div style={{ display: "flex", gap: 8, paddingBottom: 16 }}>
          {DIMENSIONS.map((d) => (
            <button
              key={d.value}
              onClick={() => setDimension(d.value)}
              style={{
                padding: "6px 12px",
                borderRadius: 999,
                border: "1px solid var(--border)",
                background: dimension === d.value ? "var(--text-primary)" : "var(--surface)",
                color: dimension === d.value ? "var(--page)" : "var(--text-secondary)",
                fontSize: 12,
                fontWeight: dimension === d.value ? 600 : 400,
                cursor: "pointer",
              }}
            >
              {d.label}
            </button>
          ))}
        </div>
        {segment.loading && <Loading />}
        {segment.error && <ErrorBlock error={segment.error} />}
        {segment.data && (
          <ResponsiveContainer width="100%" height={Math.max(180, segment.data.length * 36)}>
            <BarChart data={segment.data} layout="vertical" margin={{ top: 8, right: 24, left: 24, bottom: 0 }}>
              <CartesianGrid stroke="var(--gridline)" horizontal={false} />
              <XAxis type="number" tickFormatter={(v) => compactMoney(v)} tick={{ fontSize: 11, fill: "var(--text-muted)" }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="segment" width={120} tick={{ fontSize: 12, fill: "var(--text-secondary)" }} axisLine={false} tickLine={false} />
              <Tooltip
                formatter={(value, _n, entry) => [`${money(Number(value))} (${num(entry.payload.open_deal_count)} deals)`, entry.payload.segment]}
                contentStyle={{ background: "var(--surface-raised)", border: "1px solid var(--border)", fontSize: 12 }}
              />
              <Bar dataKey="open_pipeline_value" fill="var(--series-1)" radius={[0, 4, 4, 0]} barSize={20} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </ChartCard>
    </div>
  );
}

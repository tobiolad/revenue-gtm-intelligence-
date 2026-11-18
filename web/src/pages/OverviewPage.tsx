import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../lib/api";
import { useFetch } from "../lib/useFetch";
import { ChartCard, StatTile } from "../components/ChartCard";
import { ErrorBlock, Loading } from "../components/StatusBlock";
import { compactMoney, money, num, pct, shortMonth } from "../lib/format";

export default function OverviewPage() {
  const bookings = useFetch(() => api.bookingsTrend("month"), []);
  const pipeline = useFetch(() => api.pipelineOverview(), []);
  const winRate = useFetch(() => api.winRate(), []);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <div>
        <h1 style={{ fontSize: 22 }}>Revenue Overview</h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 13, marginTop: 4 }}>
          Bookings trend, open pipeline, and win rate across the synthetic B2B sales pipeline.
        </p>
      </div>

      {(winRate.loading || pipeline.loading) && <Loading />}
      {winRate.error && <ErrorBlock error={winRate.error} />}
      {pipeline.error && <ErrorBlock error={pipeline.error} />}
      {winRate.data && pipeline.data && (
        <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
          <StatTile label="Open pipeline" value={compactMoney(pipeline.data.open_pipeline_value)} caption={`${num(pipeline.data.open_deal_count)} open deals`} />
          <StatTile label="Win rate" value={pct(winRate.data.win_rate)} caption={`${num(winRate.data.closed_won)} won / ${num(winRate.data.closed_lost)} lost`} tone="good" />
        </div>
      )}

      <ChartCard title="Monthly bookings" subtitle="Closed-Won revenue by month of close date.">
        {bookings.loading && <Loading />}
        {bookings.error && <ErrorBlock error={bookings.error} />}
        {bookings.data && (
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={bookings.data} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
              <CartesianGrid stroke="var(--gridline)" vertical={false} />
              <XAxis
                dataKey="period"
                tickFormatter={shortMonth}
                tick={{ fontSize: 11, fill: "var(--text-muted)" }}
                axisLine={{ stroke: "var(--baseline)" }}
                tickLine={false}
                minTickGap={30}
              />
              <YAxis tickFormatter={(v) => compactMoney(v)} width={56} tick={{ fontSize: 11, fill: "var(--text-muted)" }} axisLine={false} tickLine={false} />
              <Tooltip
                labelFormatter={(v) => shortMonth(String(v))}
                formatter={(value) => money(Number(value))}
                contentStyle={{ background: "var(--surface-raised)", border: "1px solid var(--border)", fontSize: 12 }}
              />
              <Line type="monotone" dataKey="bookings" stroke="var(--series-1)" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </ChartCard>

      <ChartCard title="Open pipeline by forecast category" subtitle="Pipeline (early-stage) · Best Case (Proposal) · Commit (Negotiation).">
        {pipeline.data && (
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={pipeline.data.by_forecast_category} layout="vertical" margin={{ top: 8, right: 24, left: 24, bottom: 0 }}>
              <CartesianGrid stroke="var(--gridline)" horizontal={false} />
              <XAxis type="number" tickFormatter={(v) => compactMoney(v)} tick={{ fontSize: 11, fill: "var(--text-muted)" }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="forecast_category" width={90} tick={{ fontSize: 12, fill: "var(--text-secondary)" }} axisLine={false} tickLine={false} />
              <Tooltip
                formatter={(value, _n, entry) => [`${money(Number(value))} (${num(entry.payload.deal_count)} deals)`, entry.payload.forecast_category]}
                contentStyle={{ background: "var(--surface-raised)", border: "1px solid var(--border)", fontSize: 12 }}
              />
              <Bar dataKey="total_amount" fill="var(--series-1)" radius={[0, 4, 4, 0]} barSize={28} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </ChartCard>
    </div>
  );
}

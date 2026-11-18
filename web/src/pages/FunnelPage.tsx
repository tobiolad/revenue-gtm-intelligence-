import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../lib/api";
import { useFetch } from "../lib/useFetch";
import { ChartCard, StatTile } from "../components/ChartCard";
import { ErrorBlock, Loading } from "../components/StatusBlock";
import { days, num, pct } from "../lib/format";

// Ordinal sequential ramp (open stages), plus distinct won/lost colors for
// the two terminal stages -- those aren't "further along the same scale,"
// they're a different kind of outcome.
const STAGE_COLORS: Record<string, string> = {
  Prospecting: "var(--seq-250)",
  Qualification: "var(--seq-400)",
  Proposal: "var(--seq-500)",
  Negotiation: "var(--seq-650)",
  "Closed Won": "var(--status-good)",
  "Closed Lost": "var(--text-muted)",
};

export default function FunnelPage() {
  const funnel = useFetch(() => api.stageFunnel(), []);
  const cycle = useFetch(() => api.cycleLength(), []);
  const bySource = useFetch(() => api.winRateByLeadSource(), []);
  const byTeam = useFetch(() => api.winRateByTeam(), []);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <div>
        <h1 style={{ fontSize: 22 }}>Pipeline Funnel</h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 13, marginTop: 4 }}>
          Stage-by-stage conversion, sales cycle length, and win rate by lead source and team.
        </p>
      </div>

      <ChartCard title="Opportunities reaching each stage" subtitle="pct_of_total is always against all opportunities ever created, never the previous stage's count.">
        {funnel.loading && <Loading />}
        {funnel.error && <ErrorBlock error={funnel.error} />}
        {funnel.data && (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={funnel.data} layout="vertical" margin={{ top: 8, right: 24, left: 24, bottom: 0 }}>
              <CartesianGrid stroke="var(--gridline)" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11, fill: "var(--text-muted)" }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="stage" width={110} tick={{ fontSize: 12, fill: "var(--text-secondary)" }} axisLine={false} tickLine={false} />
              <Tooltip
                formatter={(value, _n, entry) => [`${num(Number(value))} opportunities (${pct(entry.payload.pct_of_total)} of all created)`, entry.payload.stage]}
                contentStyle={{ background: "var(--surface-raised)", border: "1px solid var(--border)", fontSize: 12 }}
              />
              <Bar dataKey="opportunities_reached" radius={[0, 4, 4, 0]}>
                {funnel.data.map((row, i) => (
                  <Cell key={i} fill={STAGE_COLORS[row.stage] ?? "var(--series-1)"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </ChartCard>

      <ChartCard title="Sales cycle length" subtitle="Days from created_date to closed_date, Won and Lost tracked separately.">
        {cycle.loading && <Loading />}
        {cycle.error && <ErrorBlock error={cycle.error} />}
        {cycle.data && (
          <div style={{ display: "flex", gap: 16, flexWrap: "wrap", paddingBottom: 16 }}>
            <StatTile label="Median days to win" value={days(cycle.data.closed_won.median_days)} tone="good" />
            <StatTile label="Mean days to win" value={days(cycle.data.closed_won.mean_days)} />
            <StatTile label="Median days to loss" value={days(cycle.data.closed_lost.median_days)} />
            <StatTile label="Mean days to loss" value={days(cycle.data.closed_lost.mean_days)} />
          </div>
        )}
      </ChartCard>

      <ChartCard title="Win rate by lead source" subtitle="Closed deals only (Won + Lost).">
        {bySource.loading && <Loading />}
        {bySource.error && <ErrorBlock error={bySource.error} />}
        {bySource.data && (
          <table>
            <thead>
              <tr>
                <th>Lead source</th>
                <th>Won</th>
                <th>Lost</th>
                <th>Win rate</th>
              </tr>
            </thead>
            <tbody>
              {bySource.data.map((row) => (
                <tr key={row.lead_source}>
                  <td>{row.lead_source}</td>
                  <td>{num(row.won)}</td>
                  <td>{num(row.lost)}</td>
                  <td style={{ fontWeight: 600 }}>{pct(row.win_rate)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </ChartCard>

      <ChartCard title="Win rate by team">
        {byTeam.loading && <Loading />}
        {byTeam.error && <ErrorBlock error={byTeam.error} />}
        {byTeam.data && (
          <table>
            <thead>
              <tr>
                <th>Team</th>
                <th>Won</th>
                <th>Lost</th>
                <th>Win rate</th>
              </tr>
            </thead>
            <tbody>
              {byTeam.data.map((row) => (
                <tr key={row.team}>
                  <td>{row.team}</td>
                  <td>{num(row.won)}</td>
                  <td>{num(row.lost)}</td>
                  <td style={{ fontWeight: 600 }}>{pct(row.win_rate)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </ChartCard>
    </div>
  );
}

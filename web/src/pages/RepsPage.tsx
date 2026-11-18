import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../lib/api";
import { useFetch } from "../lib/useFetch";
import { ChartCard } from "../components/ChartCard";
import { ErrorBlock, Loading } from "../components/StatusBlock";
import { money, num, pct } from "../lib/format";

export default function RepsPage() {
  const leaderboard = useFetch(() => api.repLeaderboard(365), []);

  const chartData = (leaderboard.data ?? [])
    .slice()
    .sort((a, b) => (b.quota_attainment ?? 0) - (a.quota_attainment ?? 0));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <div>
        <h1 style={{ fontSize: 22 }}>Rep Performance</h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 13, marginTop: 4 }}>
          Trailing-365-day bookings, win rate, and quota attainment per rep (annualized quota = monthly quota × 12).
        </p>
      </div>

      <ChartCard title="Quota attainment">
        {leaderboard.loading && <Loading />}
        {leaderboard.error && <ErrorBlock error={leaderboard.error} />}
        {leaderboard.data && (
          <ResponsiveContainer width="100%" height={Math.max(260, chartData.length * 26)}>
            <BarChart data={chartData} layout="vertical" margin={{ top: 8, right: 24, left: 24, bottom: 0 }}>
              <CartesianGrid stroke="var(--gridline)" horizontal={false} />
              <XAxis type="number" tickFormatter={(v) => pct(v, 0)} tick={{ fontSize: 11, fill: "var(--text-muted)" }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="name" width={130} tick={{ fontSize: 11, fill: "var(--text-secondary)" }} axisLine={false} tickLine={false} />
              <Tooltip
                formatter={(value, _n, entry) => [`${pct(Number(value))} (${money(entry.payload.bookings)} booked)`, entry.payload.name]}
                contentStyle={{ background: "var(--surface-raised)", border: "1px solid var(--border)", fontSize: 12 }}
              />
              <Bar dataKey="quota_attainment" radius={[0, 4, 4, 0]} barSize={14}>
                {chartData.map((row, i) => (
                  <Cell key={i} fill={(row.quota_attainment ?? 0) >= 1 ? "var(--status-good)" : "var(--series-1)"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </ChartCard>

      <ChartCard title="Leaderboard">
        {leaderboard.data && (
          <table>
            <thead>
              <tr>
                <th>Rep</th>
                <th>Team</th>
                <th>Deals won</th>
                <th>Bookings</th>
                <th>Win rate</th>
                <th>Quota attainment</th>
              </tr>
            </thead>
            <tbody>
              {leaderboard.data.map((row) => (
                <tr key={row.rep_id}>
                  <td>{row.name}</td>
                  <td>{row.team}</td>
                  <td>{num(row.deals_won)}</td>
                  <td>{money(row.bookings)}</td>
                  <td>{pct(row.win_rate)}</td>
                  <td style={{ fontWeight: 600, color: (row.quota_attainment ?? 0) >= 1 ? "var(--success-text)" : "var(--text-primary)" }}>
                    {pct(row.quota_attainment)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </ChartCard>
    </div>
  );
}

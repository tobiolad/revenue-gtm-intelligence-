import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../lib/api";
import { useFetch } from "../lib/useFetch";
import { ChartCard, StatTile } from "../components/ChartCard";
import { ErrorBlock, Loading } from "../components/StatusBlock";
import { compactMoney, money, pct, shortMonth } from "../lib/format";

export default function ForecastPage() {
  const winRates = useFetch(() => api.winRatesByStage(), []);
  const weighted = useFetch(() => api.weightedPipeline(), []);
  const monthly = useFetch(() => api.monthlyForecast(), []);
  const backtest = useFetch(() => api.backtest(), []);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <div>
        <h1 style={{ fontSize: 22 }}>Forecast</h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 13, marginTop: 4 }}>
          A pipeline-stage-weighted forecast, calibrated on historical outcomes and backtested against actual past
          bookings -- not just a point estimate asserted without evidence.
        </p>
      </div>

      <ChartCard title="Historical win rate by stage" subtitle="Among CLOSED deals that ever reached this stage (not deals whose final stage was this one) -- see docs/FORECAST_METHODOLOGY.md.">
        {winRates.loading && <Loading />}
        {winRates.error && <ErrorBlock error={winRates.error} />}
        {winRates.data && (
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={winRates.data} layout="vertical" margin={{ top: 8, right: 24, left: 24, bottom: 0 }}>
              <CartesianGrid stroke="var(--gridline)" horizontal={false} />
              <XAxis type="number" tickFormatter={(v) => pct(v, 0)} tick={{ fontSize: 11, fill: "var(--text-muted)" }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="stage" width={100} tick={{ fontSize: 12, fill: "var(--text-secondary)" }} axisLine={false} tickLine={false} />
              <Tooltip formatter={(value) => pct(Number(value))} contentStyle={{ background: "var(--surface-raised)", border: "1px solid var(--border)", fontSize: 12 }} />
              <Bar dataKey="win_rate" fill="var(--series-1)" radius={[0, 4, 4, 0]} barSize={22} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </ChartCard>

      {weighted.loading && <Loading />}
      {weighted.error && <ErrorBlock error={weighted.error} />}
      {weighted.data && (
        <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
          <StatTile label="Raw open pipeline" value={compactMoney(weighted.data.open_pipeline_value)} />
          <StatTile
            label="Stage-weighted forecast"
            value={compactMoney(weighted.data.weighted_forecast_value)}
            caption="Each open deal's amount × the historical win rate for its current stage"
            tone="good"
          />
        </div>
      )}

      <ChartCard title="Forecast by expected close month" subtitle="Open deals bucketed by their expected_close_date, raw pipeline value vs. stage-weighted forecast.">
        {monthly.loading && <Loading />}
        {monthly.error && <ErrorBlock error={monthly.error} />}
        {monthly.data && (
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={monthly.data} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
              <CartesianGrid stroke="var(--gridline)" vertical={false} />
              <XAxis dataKey="period" tickFormatter={shortMonth} tick={{ fontSize: 11, fill: "var(--text-muted)" }} axisLine={{ stroke: "var(--baseline)" }} tickLine={false} />
              <YAxis tickFormatter={(v) => compactMoney(v)} width={56} tick={{ fontSize: 11, fill: "var(--text-muted)" }} axisLine={false} tickLine={false} />
              <Tooltip labelFormatter={(v) => shortMonth(String(v))} formatter={(value) => money(Number(value))} contentStyle={{ background: "var(--surface-raised)", border: "1px solid var(--border)", fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="pipeline_value" name="Raw pipeline" fill="var(--series-1)" radius={[4, 4, 0, 0]} />
              <Bar dataKey="weighted_forecast" name="Weighted forecast" fill="var(--series-4)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </ChartCard>

      <ChartCard title="Backtest: predicted vs. actual bookings" subtitle="For every fully-elapsed month, what the weighted forecast would have said on day 1, vs. what actually closed.">
        {backtest.loading && <Loading />}
        {backtest.error && <ErrorBlock error={backtest.error} />}
        {backtest.data && (
          <>
            <div style={{ display: "flex", gap: 16, flexWrap: "wrap", paddingBottom: 16 }}>
              <StatTile
                label="Overall MAPE"
                value={pct(backtest.data.overall_mape)}
                caption={`Mean absolute % error across ${backtest.data.months_scored} of ${backtest.data.months_total} months`}
                tone="warning"
              />
            </div>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={backtest.data.by_month} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
                <CartesianGrid stroke="var(--gridline)" vertical={false} />
                <XAxis dataKey="period" tickFormatter={shortMonth} tick={{ fontSize: 11, fill: "var(--text-muted)" }} axisLine={{ stroke: "var(--baseline)" }} tickLine={false} minTickGap={20} />
                <YAxis tickFormatter={(v) => compactMoney(v)} width={56} tick={{ fontSize: 11, fill: "var(--text-muted)" }} axisLine={false} tickLine={false} />
                <Tooltip labelFormatter={(v) => shortMonth(String(v))} formatter={(value) => money(Number(value))} contentStyle={{ background: "var(--surface-raised)", border: "1px solid var(--border)", fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Bar dataKey="actual_bookings" name="Actual" fill="var(--series-1)" radius={[4, 4, 0, 0]} />
                <Bar dataKey="predicted_bookings" name="Predicted" fill="var(--series-4)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
            <p style={{ fontSize: 12, color: "var(--text-muted)", padding: "12px 0 16px" }}>
              The forecast systematically under-predicts most months -- it only counts deals that already existed
              before each month began, so it structurally misses deals created and closed within the same month.
              See docs/FORECAST_METHODOLOGY.md.
            </p>
          </>
        )}
      </ChartCard>
    </div>
  );
}

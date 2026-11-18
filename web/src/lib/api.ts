const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${path} -> ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export interface BookingsTrendRow {
  period: string;
  deals_won: number;
  bookings: number;
}

export interface PipelineCategoryRow {
  forecast_category: string;
  deal_count: number;
  total_amount: number;
}

export interface PipelineOverview {
  open_deal_count: number;
  open_pipeline_value: number;
  by_forecast_category: PipelineCategoryRow[];
}

export interface WinRateSummary {
  closed_won: number;
  closed_lost: number;
  win_rate: number | null;
}

export interface StageFunnelRow {
  stage: string;
  opportunities_reached: number;
  pct_of_total: number | null;
  pct_of_previous_stage: number | null;
}

export interface CycleStats {
  deal_count: number;
  median_days: number | null;
  mean_days: number | null;
}

export interface SalesCycleLength {
  closed_won: CycleStats;
  closed_lost: CycleStats;
}

export interface WinRateBySourceRow {
  lead_source: string;
  won: number;
  lost: number;
  win_rate: number | null;
}

export interface WinRateByTeamRow {
  team: string;
  won: number;
  lost: number;
  win_rate: number | null;
}

export interface RepLeaderboardRow {
  rep_id: string;
  name: string;
  team: string;
  quota_monthly: number;
  quota_target: number;
  deals_won: number;
  bookings: number;
  win_rate: number | null;
  quota_attainment: number | null;
}

export interface LostReasonRow {
  lost_reason: string;
  deal_count: number;
  total_amount: number;
  pct_of_losses: number;
}

export interface PipelineSegmentRow {
  segment: string;
  open_deal_count: number;
  open_pipeline_value: number;
}

export interface StageWinRateRow {
  stage: string;
  rnk: number;
  reached_count: number;
  won_count: number;
  win_rate: number;
}

export interface WeightedOpenPipeline {
  open_pipeline_value: number;
  weighted_forecast_value: number;
  weights_used: Record<string, number>;
}

export interface MonthlyForecastRow {
  period: string;
  deal_count: number;
  pipeline_value: number;
  weighted_forecast: number;
}

export interface BacktestMonthRow {
  period: string;
  actual_bookings: number;
  predicted_bookings: number;
  error: number;
  abs_pct_error: number | null;
}

export interface ForecastBacktest {
  by_month: BacktestMonthRow[];
  overall_mape: number | null;
  months_scored: number;
  months_total: number;
}

export const api = {
  bookingsTrend: (granularity: "week" | "month" = "month") =>
    get<BookingsTrendRow[]>(`/overview/bookings-trend?granularity=${granularity}`),
  pipelineOverview: () => get<PipelineOverview>("/overview/pipeline"),
  winRate: () => get<WinRateSummary>("/overview/win-rate"),
  stageFunnel: () => get<StageFunnelRow[]>("/funnel/stages"),
  cycleLength: () => get<SalesCycleLength>("/funnel/cycle-length"),
  winRateByLeadSource: () => get<WinRateBySourceRow[]>("/funnel/win-rate-by-lead-source"),
  winRateByTeam: () => get<WinRateByTeamRow[]>("/funnel/win-rate-by-team"),
  repLeaderboard: (trailingDays = 365) => get<RepLeaderboardRow[]>(`/reps/leaderboard?trailing_days=${trailingDays}`),
  lostReasons: () => get<LostReasonRow[]>("/deals/lost-reasons"),
  pipelineBySegment: (dimension: "industry" | "region" | "employee_band" = "industry") =>
    get<PipelineSegmentRow[]>(`/deals/pipeline-by-segment?dimension=${dimension}`),
  winRatesByStage: () => get<StageWinRateRow[]>("/forecast/win-rates-by-stage"),
  weightedPipeline: () => get<WeightedOpenPipeline>("/forecast/weighted-pipeline"),
  monthlyForecast: () => get<MonthlyForecastRow[]>("/forecast/monthly"),
  backtest: () => get<ForecastBacktest>("/forecast/backtest"),
};

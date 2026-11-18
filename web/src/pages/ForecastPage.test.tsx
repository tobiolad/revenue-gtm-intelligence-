import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import ForecastPage from "./ForecastPage";
import { api } from "../lib/api";

vi.mock("../lib/api", () => ({
  api: {
    winRatesByStage: vi.fn(),
    weightedPipeline: vi.fn(),
    monthlyForecast: vi.fn(),
    backtest: vi.fn(),
  },
}));

const WIN_RATES = [
  { stage: "Prospecting", rnk: 1, reached_count: 2744, won_count: 628, win_rate: 0.2289 },
  { stage: "Qualification", rnk: 2, reached_count: 1900, won_count: 628, win_rate: 0.3305 },
  { stage: "Proposal", rnk: 3, reached_count: 1312, won_count: 628, win_rate: 0.4787 },
  { stage: "Negotiation", rnk: 4, reached_count: 890, won_count: 628, win_rate: 0.7056 },
];

const WEIGHTED_PIPELINE = {
  open_pipeline_value: 4434353.0,
  weighted_forecast_value: 2134908.02,
  weights_used: { Prospecting: 0.2289, Qualification: 0.3305, Proposal: 0.4787, Negotiation: 0.7056 },
};

const MONTHLY_FORECAST = [{ period: "2026-08-01T00:00:00", deal_count: 63, pipeline_value: 1073931.35, weighted_forecast: 488552.33 }];

const BACKTEST = {
  by_month: [
    { period: "2026-01", actual_bookings: 714741.37, predicted_bookings: 415067.16, error: -299674.21, abs_pct_error: 0.4193 },
    { period: "2024-10", actual_bookings: 0, predicted_bookings: 0, error: 0, abs_pct_error: null },
  ],
  overall_mape: 0.3667,
  months_scored: 20,
  months_total: 21,
};

function mockAllResolved() {
  vi.mocked(api.winRatesByStage).mockResolvedValue(WIN_RATES);
  vi.mocked(api.weightedPipeline).mockResolvedValue(WEIGHTED_PIPELINE);
  vi.mocked(api.monthlyForecast).mockResolvedValue(MONTHLY_FORECAST);
  vi.mocked(api.backtest).mockResolvedValue(BACKTEST);
}

describe("ForecastPage", () => {
  it("shows a loading state before the win-rate-by-stage data resolves", () => {
    vi.mocked(api.winRatesByStage).mockReturnValue(new Promise(() => {}));
    vi.mocked(api.weightedPipeline).mockReturnValue(new Promise(() => {}));
    vi.mocked(api.monthlyForecast).mockReturnValue(new Promise(() => {}));
    vi.mocked(api.backtest).mockReturnValue(new Promise(() => {}));
    render(<ForecastPage />);
    expect(screen.getAllByText(/Loading/).length).toBeGreaterThan(0);
  });

  it("renders the weighted pipeline stat tiles and backtest MAPE once data loads", async () => {
    mockAllResolved();
    render(<ForecastPage />);

    await waitFor(() => expect(screen.getByText("$4.4M")).toBeInTheDocument());
    expect(screen.getByText("$2.1M")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("36.7%")).toBeInTheDocument());
    expect(screen.getByText(/20 of 21 months/)).toBeInTheDocument();
  });

  it("shows the under-prediction caveat once the backtest loads", async () => {
    mockAllResolved();
    render(<ForecastPage />);
    await waitFor(() => expect(screen.getByText(/systematically under-predicts/)).toBeInTheDocument());
  });

  it("shows an error state when a request fails", async () => {
    vi.mocked(api.winRatesByStage).mockRejectedValue(new Error("network down"));
    vi.mocked(api.weightedPipeline).mockResolvedValue(WEIGHTED_PIPELINE);
    vi.mocked(api.monthlyForecast).mockResolvedValue(MONTHLY_FORECAST);
    vi.mocked(api.backtest).mockResolvedValue(BACKTEST);
    render(<ForecastPage />);
    await waitFor(() => expect(screen.getByText(/Couldn't load this data/)).toBeInTheDocument());
    expect(screen.getByText(/network down/)).toBeInTheDocument();
  });
});

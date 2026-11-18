import pandas as pd
import pytest

import forecast as f


class TestHistoricalWinRateByStage:
    def test_rates_match_hand_count_of_closed_deals(self, con):
        """
        Closed deals: OPP-1 (won, reached all 4 stages), OPP-2 (lost,
        reached Prospecting+Qualification), OPP-3 (lost, reached
        Prospecting only), OPP-4 (won, reached all 4 stages).

        "Reached >= stage" among closed deals:
          Prospecting:   OPP-1,2,3,4 (4) -> 2 won -> 0.5
          Qualification: OPP-1,2,4   (3) -> 2 won -> 0.6667
          Proposal:      OPP-1,4     (2) -> 2 won -> 1.0
          Negotiation:   OPP-1,4     (2) -> 2 won -> 1.0
        """
        rates = f.historical_win_rate_by_stage(con).set_index("stage")
        assert rates.loc["Prospecting", "reached_count"] == 4
        assert rates.loc["Prospecting", "won_count"] == 2
        assert rates.loc["Prospecting", "win_rate"] == pytest.approx(0.5)
        assert rates.loc["Qualification", "reached_count"] == 3
        assert rates.loc["Qualification", "win_rate"] == pytest.approx(2 / 3, abs=1e-4)
        assert rates.loc["Proposal", "win_rate"] == pytest.approx(1.0)
        assert rates.loc["Negotiation", "win_rate"] == pytest.approx(1.0)

    def test_rates_are_never_degenerate_zero_for_early_stages(self, con):
        """
        The whole point of using "ever reached" rather than "final stage"
        is that an early stage's rate reflects deals that are STILL IN
        PROGRESS toward a possible win, not "0% because winning requires
        later stages" -- that tautology is exactly the bug this metric is
        designed around (see db/forecast.py module docstring).
        """
        rates = f.historical_win_rate_by_stage(con).set_index("stage")
        assert rates.loc["Prospecting", "win_rate"] > 0
        assert rates.loc["Qualification", "win_rate"] > 0


class TestWeightedOpenPipeline:
    def test_weighted_value_matches_hand_calculation(self, con):
        # weights: Prospecting=0.5, Qualification=0.6667, Proposal=1.0, Negotiation=1.0
        # OPP-5 Proposal $8,000 * 1.0 = 8,000
        # OPP-6 Qualification $12,000 * 0.6667 = 8,000.4
        # OPP-7 Prospecting $9,000 * 0.5 = 4,500
        # OPP-8 Negotiation $25,000 * 1.0 = 25,000
        # OPP-9 Qualification $16,000 * 0.6667 = 10,667.2
        result = f.weighted_open_pipeline(con)
        assert result["open_pipeline_value"] == pytest.approx(70000.0)
        assert result["weighted_forecast_value"] == pytest.approx(8000 + 8000.4 + 4500 + 25000 + 10667.2, abs=1.0)

    def test_weighted_value_is_always_less_than_raw_pipeline(self, con):
        """A win rate is a fraction in [0, 1] applied to real deal amounts, so weighting can only shrink the total, never grow it."""
        result = f.weighted_open_pipeline(con)
        assert result["weighted_forecast_value"] < result["open_pipeline_value"]


class TestWeightedPipelineForecast:
    def test_monthly_buckets_match_hand_calculation(self, con):
        forecast = f.weighted_pipeline_forecast(con).set_index("period")
        feb_row = forecast[(forecast.index.astype(str).str.startswith("2026-02"))]
        assert feb_row["deal_count"].iloc[0] == 3
        assert feb_row["pipeline_value"].iloc[0] == pytest.approx(45000.0)
        assert feb_row["weighted_forecast"].iloc[0] == pytest.approx(8000 + 8000.4 + 25000, abs=1.0)

        mar_row = forecast[(forecast.index.astype(str).str.startswith("2026-03"))]
        assert mar_row["deal_count"].iloc[0] == 1
        assert mar_row["pipeline_value"].iloc[0] == pytest.approx(9000.0)


class TestForecastAccuracyBacktest:
    def test_december_is_unscored_with_no_visible_candidates_and_no_actual_bookings(self, con):
        """
        The backtest window spans every month from the earliest created_date
        (OPP-9, 2025-12-01) to the month before the latest closed_date
        (2026-02-05 -> February excluded as not fully elapsed), so December
        2025 and January 2026 are both in scope. December has zero actual
        Closed-Won bookings (nothing closes that month) AND zero visible
        candidates (OPP-9 was created ON 2025-12-01, not before it, so it
        isn't yet "existing" as of that same-day snapshot) -- a genuine
        0-vs-0 month, correctly left out of the scored MAPE average rather
        than contributing a fake 0% or undefined error.
        """
        result = f.forecast_accuracy_backtest(con)
        assert result["months_total"] == 2
        assert result["months_scored"] == 1

        dec_row = result["by_month"].set_index("period").loc["2025-12"]
        assert dec_row["actual_bookings"] == pytest.approx(0.0)
        assert dec_row["predicted_bookings"] == pytest.approx(0.0)
        assert dec_row["abs_pct_error"] is None or pd.isna(dec_row["abs_pct_error"])

    def test_scores_january_using_the_one_visible_candidate(self, con):
        """
        As of a 2026-01-01 snapshot, OPP-9 is the only deal that existed
        before that day. It had reached Qualification by then (win rate
        0.6667), so predicted = 16000 * 0.6667 = 10,667.2. Actual January
        Closed-Won bookings = OPP-1 only ($10,000) -- OPP-4 closes in
        February, outside this month.
        """
        result = f.forecast_accuracy_backtest(con)
        jan_row = result["by_month"].set_index("period").loc["2026-01"]
        assert jan_row["actual_bookings"] == pytest.approx(10000.0)
        assert jan_row["predicted_bookings"] == pytest.approx(16000 * 0.6667, abs=1.0)
        assert jan_row["abs_pct_error"] == pytest.approx(abs(16000 * 0.6667 - 10000) / 10000, abs=1e-3)

    def test_overall_mape_matches_the_single_month(self, con):
        result = f.forecast_accuracy_backtest(con)
        expected_mape = abs(16000 * 0.6667 - 10000) / 10000
        assert result["overall_mape"] == pytest.approx(expected_mape, abs=1e-3)

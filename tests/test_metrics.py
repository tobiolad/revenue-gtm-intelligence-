import pandas as pd
import pytest

import metrics as m


class TestStageFunnel:
    def test_counts_and_percentages_match_hand_count(self, con):
        funnel = m.stage_funnel(con).set_index("stage")
        # 9 opportunities total; Prospecting reached by all 9.
        assert funnel.loc["Prospecting", "opportunities_reached"] == 9
        assert funnel.loc["Prospecting", "pct_of_total"] == pytest.approx(1.0)
        # Qualification: everyone except OPP-3 (lost at Prospecting) and OPP-7 (still at Prospecting).
        assert funnel.loc["Qualification", "opportunities_reached"] == 7
        assert funnel.loc["Proposal", "opportunities_reached"] == 4  # OPP-1,4,5,8
        assert funnel.loc["Negotiation", "opportunities_reached"] == 3  # OPP-1,4,8
        assert funnel.loc["Closed Won", "opportunities_reached"] == 2  # OPP-1,4
        assert funnel.loc["Closed Lost", "opportunities_reached"] == 2  # OPP-2,3

    def test_closed_lost_has_no_pct_of_previous_stage(self, con):
        """Losses branch off from every stage, not just Negotiation -- a single prior-stage ratio would be meaningless."""
        funnel = m.stage_funnel(con).set_index("stage")
        assert pd.isna(funnel.loc["Closed Lost", "pct_of_previous_stage"])

    def test_closed_won_pct_of_previous_stage_is_real(self, con):
        funnel = m.stage_funnel(con).set_index("stage")
        # 2 of the 3 opportunities that reached Negotiation went on to win.
        assert funnel.loc["Closed Won", "pct_of_previous_stage"] == pytest.approx(2 / 3, abs=1e-4)


class TestWinRate:
    def test_overall_win_rate(self, con):
        result = m.win_rate(con)
        assert result == {"closed_won": 2, "closed_lost": 2, "win_rate": 0.5}

    def test_win_rate_by_lead_source(self, con):
        by_source = m.win_rate_by_lead_source(con).set_index("lead_source")
        assert by_source.loc["Referral", "win_rate"] == pytest.approx(0.5)  # OPP-1 won, OPP-2 lost
        assert by_source.loc["Outbound", "win_rate"] == pytest.approx(0.5)  # OPP-4 won, OPP-3 lost

    def test_win_rate_by_team(self, con):
        by_team = m.win_rate_by_team(con).set_index("team")
        assert by_team.loc["SMB", "win_rate"] == pytest.approx(0.5)
        assert by_team.loc["Enterprise", "win_rate"] == pytest.approx(0.5)


class TestSalesCycleLength:
    def test_closed_won_cycle(self, con):
        result = m.sales_cycle_length(con)
        # OPP-1: Jan 1 -> Jan 15 = 14 days. OPP-4: Jan 1 -> Feb 5 = 35 days.
        assert result["closed_won"]["deal_count"] == 2
        assert result["closed_won"]["median_days"] == pytest.approx((14 + 35) / 2)

    def test_closed_lost_cycle(self, con):
        result = m.sales_cycle_length(con)
        # OPP-2: Jan 1 -> Jan 10 = 9 days. OPP-3: Jan 1 -> Jan 5 = 4 days.
        assert result["closed_lost"]["deal_count"] == 2
        assert result["closed_lost"]["median_days"] == pytest.approx(6.5)


class TestPipelineOverview:
    def test_totals_and_category_breakdown(self, con):
        overview = m.pipeline_overview(con)
        # Open: OPP-5,6,7,8,9 = 8000+12000+9000+25000+16000 = 70000
        assert overview["open_deal_count"] == 5
        assert overview["open_pipeline_value"] == pytest.approx(70000.0)
        by_cat = overview["by_forecast_category"].set_index("forecast_category")
        assert by_cat.loc["Pipeline", "deal_count"] == 3  # OPP-6,7,9
        assert by_cat.loc["Best Case", "deal_count"] == 1  # OPP-5
        assert by_cat.loc["Commit", "deal_count"] == 1  # OPP-8


class TestRepLeaderboard:
    def test_attainment_over_a_window_covering_all_closed_deals(self, con):
        # as_of = MAX(closed_date) = 2026-02-05 (OPP-4). A 60-day trailing
        # window reaches back to 2025-12-07, comfortably covering every
        # closed deal (earliest close is 2026-01-05).
        board = m.rep_leaderboard(con, trailing_days=60).set_index("rep_id")
        assert board.loc["REP-1", "deals_won"] == 1  # OPP-1
        assert board.loc["REP-1", "bookings"] == pytest.approx(10000.0)
        assert board.loc["REP-1", "win_rate"] == pytest.approx(0.5)
        assert board.loc["REP-1", "quota_attainment"] == pytest.approx(10000 / 20000)  # quota_target = 10000 * 60/30
        assert board.loc["REP-2", "deals_won"] == 1  # OPP-4
        assert board.loc["REP-2", "bookings"] == pytest.approx(15000.0)
        assert board.loc["REP-2", "quota_attainment"] == pytest.approx(15000 / 40000)


class TestLostReasonBreakdown:
    def test_two_losses_with_distinct_reasons(self, con):
        breakdown = m.lost_reason_breakdown(con).set_index("lost_reason")
        assert breakdown.loc["Price", "deal_count"] == 1
        assert breakdown.loc["Price", "total_amount"] == pytest.approx(5000.0)
        assert breakdown.loc["Budget", "deal_count"] == 1
        assert breakdown.loc["Budget", "total_amount"] == pytest.approx(20000.0)
        assert breakdown.loc["Price", "pct_of_losses"] == pytest.approx(0.5)

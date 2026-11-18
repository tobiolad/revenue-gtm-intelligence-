"""
Exercises the API against the real built database (generator/generate.py +
db/load.py must have been run first). These are integration tests of the
HTTP layer and response shapes; metric/forecast correctness is covered by
tests/test_metrics.py and tests/test_forecast.py against a hand-crafted
fixture.
"""
import pytest
from fastapi.testclient import TestClient

from app.db import DB_PATH
from app.main import app

pytestmark = pytest.mark.skipif(
    not DB_PATH.exists(), reason="db/gtm.duckdb not built -- run generator/generate.py then db/load.py first"
)

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


class TestOverview:
    def test_bookings_trend_month(self):
        resp = client.get("/overview/bookings-trend")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) > 0
        assert {"period", "deals_won", "bookings"} <= body[0].keys()

    def test_bookings_trend_rejects_bad_granularity(self):
        resp = client.get("/overview/bookings-trend", params={"granularity": "year"})
        assert resp.status_code == 422

    def test_pipeline(self):
        resp = client.get("/overview/pipeline")
        assert resp.status_code == 200
        body = resp.json()
        assert body["open_deal_count"] > 0
        assert len(body["by_forecast_category"]) > 0

    def test_win_rate(self):
        resp = client.get("/overview/win-rate")
        assert resp.status_code == 200
        body = resp.json()
        assert 0 <= body["win_rate"] <= 1


class TestFunnel:
    def test_stages_in_order(self):
        resp = client.get("/funnel/stages")
        assert resp.status_code == 200
        stages = [row["stage"] for row in resp.json()]
        assert stages == ["Prospecting", "Qualification", "Proposal", "Negotiation", "Closed Won", "Closed Lost"]

    def test_closed_lost_has_no_pct_of_previous_stage(self):
        resp = client.get("/funnel/stages")
        rows = {row["stage"]: row for row in resp.json()}
        assert rows["Closed Lost"]["pct_of_previous_stage"] is None

    def test_cycle_length(self):
        resp = client.get("/funnel/cycle-length")
        assert resp.status_code == 200
        body = resp.json()
        assert "closed_won" in body and "closed_lost" in body
        assert body["closed_won"]["deal_count"] > 0

    def test_win_rate_by_lead_source_shows_meaningful_spread(self):
        resp = client.get("/funnel/win-rate-by-lead-source")
        assert resp.status_code == 200
        rates = [row["win_rate"] for row in resp.json() if row["win_rate"] is not None]
        assert max(rates) - min(rates) > 0.2

    def test_win_rate_by_team(self):
        resp = client.get("/funnel/win-rate-by-team")
        assert resp.status_code == 200
        assert len(resp.json()) == 3  # Enterprise, Mid-Market, SMB


class TestReps:
    def test_leaderboard_default(self):
        resp = client.get("/reps/leaderboard")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 18  # N_REPS

    def test_leaderboard_rejects_out_of_range_trailing_days(self):
        resp = client.get("/reps/leaderboard", params={"trailing_days": 9999})
        assert resp.status_code == 422


class TestDeals:
    def test_lost_reasons(self):
        resp = client.get("/deals/lost-reasons")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 5  # LOST_REASONS
        assert abs(sum(row["pct_of_losses"] for row in body) - 1.0) < 1e-3

    def test_pipeline_by_segment_industry(self):
        resp = client.get("/deals/pipeline-by-segment", params={"dimension": "industry"})
        assert resp.status_code == 200
        assert len(resp.json()) > 0

    def test_pipeline_by_segment_rejects_unknown_dimension(self):
        resp = client.get("/deals/pipeline-by-segment", params={"dimension": "account_group; DROP TABLE accounts"})
        assert resp.status_code == 422


class TestForecast:
    def test_win_rates_by_stage_is_monotonic(self):
        resp = client.get("/forecast/win-rates-by-stage")
        assert resp.status_code == 200
        rates = [row["win_rate"] for row in resp.json()]
        assert rates == sorted(rates)  # Prospecting -> Negotiation should only ever increase

    def test_weighted_pipeline_is_below_raw_pipeline(self):
        resp = client.get("/forecast/weighted-pipeline")
        assert resp.status_code == 200
        body = resp.json()
        assert body["weighted_forecast_value"] < body["open_pipeline_value"]

    def test_monthly_forecast(self):
        resp = client.get("/forecast/monthly")
        assert resp.status_code == 200
        assert len(resp.json()) > 0

    def test_backtest(self):
        resp = client.get("/forecast/backtest")
        assert resp.status_code == 200
        body = resp.json()
        assert body["months_total"] > 0
        assert 0 <= body["overall_mape"]

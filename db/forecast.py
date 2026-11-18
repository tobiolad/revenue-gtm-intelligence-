"""
Pipeline forecasting: derives an empirical win rate per pipeline stage
from historical deals, uses it to produce a probability-weighted forecast
of future bookings, and backtests that exact weighting scheme against
actual historical bookings to report how accurate it would have been.
See docs/FORECAST_METHODOLOGY.md for the full write-up of what this does
and does not claim.
"""
from __future__ import annotations

import duckdb
import pandas as pd

OPEN_STAGE_RANK = {"Prospecting": 1, "Qualification": 2, "Proposal": 3, "Negotiation": 4}
STAGE_TO_CATEGORY = {"Prospecting": "Pipeline", "Qualification": "Pipeline", "Proposal": "Best Case", "Negotiation": "Commit"}


def historical_win_rate_by_stage(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """
    For each pipeline stage, the empirical Closed-Won rate among CLOSED
    deals that ever REACHED that stage (not deals whose final/last stage
    was that one -- in a strictly sequential funnel, only deals that reach
    Negotiation can ever win, so "win rate of deals that ended in
    Prospecting" is 0% by construction and useless as a weight. "Win rate
    of deals that at some point passed through Prospecting" is the
    standard, well-behaved CRM calibration: it is the overall win rate at
    the earliest stage and rises monotonically toward Negotiation.
    """
    return con.execute(
        """
        WITH stage_rank(stage, rnk) AS (
            VALUES ('Prospecting', 1), ('Qualification', 2), ('Proposal', 3), ('Negotiation', 4)
        ),
        reached AS (
            SELECT DISTINCT sp.opp_id, sr.stage, sr.rnk
            FROM stage_progress sp
            JOIN stage_rank sr ON sr.stage = sp.stage
        ),
        closed_outcomes AS (
            SELECT opp_id, stage AS final_stage FROM opportunities WHERE status = 'Closed'
        )
        SELECT
            r.stage,
            r.rnk,
            COUNT(*) AS reached_count,
            COUNT(*) FILTER (WHERE co.final_stage = 'Closed Won') AS won_count,
            ROUND(COUNT(*) FILTER (WHERE co.final_stage = 'Closed Won') * 1.0 / COUNT(*), 4) AS win_rate
        FROM reached r
        JOIN closed_outcomes co ON co.opp_id = r.opp_id
        GROUP BY r.stage, r.rnk
        ORDER BY r.rnk
        """
    ).df()


def _stage_weight_map(con: duckdb.DuckDBPyConnection) -> dict:
    rates = historical_win_rate_by_stage(con)
    return dict(zip(rates.stage, rates.win_rate))


def weighted_open_pipeline(con: duckdb.DuckDBPyConnection) -> dict:
    """
    Single current snapshot: every open deal's amount weighted by the
    historical win rate for its current stage, summed -- "if history
    repeats, this is roughly what the current pipeline is worth in
    expected bookings."
    """
    weight_map = _stage_weight_map(con)
    open_deals = con.execute("SELECT stage, amount FROM opportunities WHERE status = 'Open'").df()
    open_deals["weight"] = open_deals.stage.map(weight_map)
    weighted_value = float((open_deals.amount * open_deals.weight).sum())
    return {
        "open_pipeline_value": round(float(open_deals.amount.sum()), 2),
        "weighted_forecast_value": round(weighted_value, 2),
        "weights_used": weight_map,
    }


def weighted_pipeline_forecast(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """
    Open deals bucketed by the month of their expected_close_date (the
    rep's own target, set at creation) and by forecast category (for
    familiar display grouping), weighted deal-by-deal using the historical
    win rate for each deal's current STAGE (finer-grained than the
    3-category display, since Pipeline covers two stages with different
    win rates). Reports both the raw (unweighted) pipeline value and the
    weighted forecast per month.
    """
    weight_map = _stage_weight_map(con)
    open_deals = con.execute(
        """
        SELECT date_trunc('month', expected_close_date) AS period, forecast_category, stage, amount
        FROM opportunities
        WHERE status = 'Open'
        """
    ).df()
    open_deals["weight"] = open_deals.stage.map(weight_map)
    open_deals["weighted_amount"] = open_deals.amount * open_deals.weight

    grouped = (
        open_deals.groupby("period", as_index=False)
        .agg(deal_count=("amount", "size"), pipeline_value=("amount", "sum"), weighted_forecast=("weighted_amount", "sum"))
        .sort_values("period")
    )
    grouped["pipeline_value"] = grouped.pipeline_value.round(2)
    grouped["weighted_forecast"] = grouped.weighted_forecast.round(2)
    return grouped


def forecast_accuracy_backtest(con: duckdb.DuckDBPyConnection) -> dict:
    """
    For every fully-elapsed calendar month in the data, reconstructs what
    the stage-weighted forecast WOULD have said on day 1 of that month --
    using only deals that existed and were still open at that moment,
    bucketed by their expected_close_date into that month, weighted by
    each deal's STAGE AS OF that snapshot date (not its final stage) --
    and compares the total to actual Closed-Won bookings that month. This
    is a true point-in-time backtest: every ingredient is reconstructed
    from stage_progress as it would have looked on that day, never read
    from a deal's eventual outcome.
    """
    opps = con.execute(
        "SELECT opp_id, amount, created_date, expected_close_date, closed_date, stage, status FROM opportunities"
    ).df()
    for col in ("created_date", "expected_close_date", "closed_date"):
        opps[col] = pd.to_datetime(opps[col])

    progress = con.execute(
        "SELECT opp_id, stage, entered_at FROM stage_progress WHERE stage IN ('Prospecting', 'Qualification', 'Proposal', 'Negotiation')"
    ).df()
    progress["entered_at"] = pd.to_datetime(progress.entered_at)
    progress["rnk"] = progress.stage.map(OPEN_STAGE_RANK)
    rank_to_stage = {v: k for k, v in OPEN_STAGE_RANK.items()}

    weight_map = _stage_weight_map(con)

    cutoff = opps.closed_date.max().normalize()
    months = pd.period_range(opps.created_date.min().to_period("M"), cutoff.to_period("M") - 1, freq="M")

    rows = []
    for month in months:
        snapshot = month.start_time
        month_end = month.end_time.normalize()

        actual = opps.loc[
            (opps.stage == "Closed Won") & (opps.closed_date >= snapshot) & (opps.closed_date <= month_end), "amount"
        ].sum()

        candidates = opps[
            (opps.created_date < snapshot)
            & (opps.closed_date.isna() | (opps.closed_date >= snapshot))
            & (opps.expected_close_date >= snapshot)
            & (opps.expected_close_date <= month_end)
        ]

        predicted = 0.0
        if not candidates.empty:
            relevant_progress = progress[progress.opp_id.isin(candidates.opp_id) & (progress.entered_at <= snapshot)]
            rank_as_of_snapshot = relevant_progress.groupby("opp_id")["rnk"].max()
            cand = candidates.set_index("opp_id").copy()
            cand["rank_as_of_snapshot"] = rank_as_of_snapshot
            cand = cand.dropna(subset=["rank_as_of_snapshot"])
            cand["stage_as_of_snapshot"] = cand["rank_as_of_snapshot"].map(rank_to_stage)
            cand["weight"] = cand["stage_as_of_snapshot"].map(weight_map)
            predicted = float((cand.amount * cand.weight).sum())

        actual = float(actual)
        rows.append({
            "period": str(month),
            "actual_bookings": round(actual, 2),
            "predicted_bookings": round(predicted, 2),
            "error": round(predicted - actual, 2),
            "abs_pct_error": round(abs(predicted - actual) / actual, 4) if actual > 0 else None,
        })

    by_month = pd.DataFrame(rows)
    scored = by_month.abs_pct_error.dropna()
    overall_mape = round(float(scored.mean()), 4) if len(scored) else None

    return {
        "by_month": by_month,
        "overall_mape": overall_mape,
        "months_scored": int(len(scored)),
        "months_total": int(len(by_month)),
    }

"""
Revenue/GTM pipeline metrics, each a single documented SQL query against
the canonical `opportunities` / `stage_progress` tables/views. See
docs/METRIC_DEFINITIONS.md for the prose definition of every metric here --
these functions are its executable form, not a separate reimplementation.

All functions take a duckdb connection and return a pandas DataFrame
(or a dict for single-row summaries).
"""
from __future__ import annotations

import duckdb
import pandas as pd

OPEN_STAGE_ORDER = ["Prospecting", "Qualification", "Proposal", "Negotiation"]


def bookings_trend(con: duckdb.DuckDBPyConnection, granularity: str = "month"):
    """Closed-Won bookings (sum of deal amount) and deal count, by month or week of close date."""
    if granularity not in ("month", "week"):
        raise ValueError("granularity must be 'month' or 'week'")
    bucket_expr = f"date_trunc('{granularity}', closed_date)"
    return con.execute(
        f"""
        SELECT {bucket_expr} AS period, COUNT(*) AS deals_won, ROUND(SUM(amount), 2) AS bookings
        FROM opportunities
        WHERE stage = 'Closed Won'
        GROUP BY 1
        ORDER BY 1
        """
    ).df()


def pipeline_overview(con: duckdb.DuckDBPyConnection) -> dict:
    """
    Headline open-pipeline numbers: total value/count, and the same broken
    out by forecast category (Pipeline / Best Case / Commit). Unweighted --
    see db/forecast.py for the probability-weighted version.
    """
    total = con.execute(
        "SELECT COUNT(*), ROUND(SUM(amount), 2) FROM opportunities WHERE status = 'Open'"
    ).fetchone()
    by_category = con.execute(
        """
        SELECT forecast_category, COUNT(*) AS deal_count, ROUND(SUM(amount), 2) AS total_amount
        FROM opportunities
        WHERE status = 'Open'
        GROUP BY 1
        ORDER BY 1
        """
    ).df()
    return {
        "open_deal_count": total[0],
        "open_pipeline_value": total[1],
        "by_forecast_category": by_category,
    }


def stage_funnel(con: duckdb.DuckDBPyConnection):
    """
    Each stage's share of all opportunities ever created
    ("pct_of_total", a constant denominator across every stage, not the
    previous stage's count), plus "pct_of_previous_stage" for classic
    funnel drop-off reading along the ordered open-stage chain. Stage
    order is fixed and matches generator/constants.py OPEN_STAGES.

    "Closed Lost" is reported but given no pct_of_previous_stage: deals
    are lost FROM any open stage, not only from Negotiation, so its count
    is an aggregate across every branch point, not one sequential
    transition -- dividing it by Negotiation's count would produce a
    number over 100% that looks like an error but isn't a drop-off at all.
    "Closed Won" keeps a real pct_of_previous_stage (of Negotiation), since
    winning only happens by advancing out of Negotiation.
    """
    stages = OPEN_STAGE_ORDER + ["Closed Won", "Closed Lost"]
    total = con.execute("SELECT COUNT(*) FROM opportunities").fetchone()[0]

    rows = []
    prev_count = total
    for stage in stages:
        count = con.execute(
            "SELECT COUNT(DISTINCT opp_id) FROM stage_progress WHERE stage = ?", [stage]
        ).fetchone()[0]
        pct_of_previous = round(count / prev_count, 4) if stage != "Closed Lost" and prev_count else None
        rows.append({
            "stage": stage,
            "opportunities_reached": count,
            "pct_of_total": round(count / total, 4) if total else None,
            "pct_of_previous_stage": pct_of_previous,
        })
        if stage in OPEN_STAGE_ORDER:
            prev_count = count
    return pd.DataFrame(rows)


def win_rate(con: duckdb.DuckDBPyConnection) -> dict:
    """Win rate = Closed Won / (Closed Won + Closed Lost). Open deals are excluded -- they haven't resolved yet."""
    row = con.execute(
        """
        SELECT
            COUNT(*) FILTER (WHERE stage = 'Closed Won') AS won,
            COUNT(*) FILTER (WHERE stage = 'Closed Lost') AS lost
        FROM opportunities
        WHERE status = 'Closed'
        """
    ).fetchone()
    won, lost = row
    total = won + lost
    return {"closed_won": won, "closed_lost": lost, "win_rate": round(won / total, 4) if total else None}


def win_rate_by_lead_source(con: duckdb.DuckDBPyConnection):
    return con.execute(
        """
        SELECT
            COALESCE(lead_source, 'Unknown') AS lead_source,
            COUNT(*) FILTER (WHERE stage = 'Closed Won') AS won,
            COUNT(*) FILTER (WHERE stage = 'Closed Lost') AS lost,
            ROUND(
                COUNT(*) FILTER (WHERE stage = 'Closed Won') * 1.0
                / NULLIF(COUNT(*) FILTER (WHERE stage IN ('Closed Won', 'Closed Lost')), 0),
                4
            ) AS win_rate
        FROM opportunities
        WHERE status = 'Closed'
        GROUP BY 1
        ORDER BY win_rate DESC NULLS LAST
        """
    ).df()


def win_rate_by_team(con: duckdb.DuckDBPyConnection):
    return con.execute(
        """
        SELECT
            r.team,
            COUNT(*) FILTER (WHERE o.stage = 'Closed Won') AS won,
            COUNT(*) FILTER (WHERE o.stage = 'Closed Lost') AS lost,
            ROUND(
                COUNT(*) FILTER (WHERE o.stage = 'Closed Won') * 1.0
                / NULLIF(COUNT(*) FILTER (WHERE o.stage IN ('Closed Won', 'Closed Lost')), 0),
                4
            ) AS win_rate
        FROM opportunities o
        JOIN sales_reps r ON r.rep_id = o.owner_id
        WHERE o.status = 'Closed'
        GROUP BY 1
        ORDER BY win_rate DESC NULLS LAST
        """
    ).df()


def sales_cycle_length(con: duckdb.DuckDBPyConnection) -> dict:
    """
    Median/mean days from created_date to closed_date, for Closed Won and
    Closed Lost separately -- lost deals often resolve on a different
    timeline than won ones, so averaging them together would misrepresent
    both.
    """
    def _one(stage: str) -> dict:
        row = con.execute(
            """
            SELECT
                COUNT(*),
                ROUND(MEDIAN(date_diff('day', created_date, closed_date)), 1),
                ROUND(AVG(date_diff('day', created_date, closed_date)), 1)
            FROM opportunities
            WHERE stage = ?
            """,
            [stage],
        ).fetchone()
        return {"deal_count": row[0], "median_days": row[1], "mean_days": row[2]}

    return {"closed_won": _one("Closed Won"), "closed_lost": _one("Closed Lost")}


def rep_leaderboard(con: duckdb.DuckDBPyConnection, trailing_days: int = 365):
    """
    Per-rep bookings, deal count, win rate, and quota attainment over the
    trailing `trailing_days` window (annualized quota = quota_monthly * 12
    by default, to match a 365-day trailing window). "As of" is the latest
    closed_date in the data, not wall-clock today, so this stays meaningful
    however old the dataset is.
    """
    return con.execute(
        f"""
        WITH as_of AS (SELECT MAX(closed_date) AS d FROM opportunities WHERE status = 'Closed'),
        closed_recent AS (
            SELECT o.*
            FROM opportunities o, as_of
            WHERE o.status = 'Closed' AND o.closed_date > as_of.d - INTERVAL '{trailing_days} days'
        )
        SELECT
            r.rep_id,
            r.name,
            r.team,
            r.quota_monthly,
            ROUND(r.quota_monthly * {trailing_days} / 30.0, 2) AS quota_target,
            COUNT(*) FILTER (WHERE c.stage = 'Closed Won') AS deals_won,
            ROUND(COALESCE(SUM(c.amount) FILTER (WHERE c.stage = 'Closed Won'), 0), 2) AS bookings,
            ROUND(
                COUNT(*) FILTER (WHERE c.stage = 'Closed Won') * 1.0
                / NULLIF(COUNT(*) FILTER (WHERE c.stage IN ('Closed Won', 'Closed Lost')), 0),
                4
            ) AS win_rate,
            ROUND(
                COALESCE(SUM(c.amount) FILTER (WHERE c.stage = 'Closed Won'), 0)
                / NULLIF(r.quota_monthly * {trailing_days} / 30.0, 0),
                4
            ) AS quota_attainment
        FROM sales_reps r
        LEFT JOIN closed_recent c ON c.owner_id = r.rep_id
        GROUP BY r.rep_id, r.name, r.team, r.quota_monthly
        ORDER BY bookings DESC
        """
    ).df()


def lost_reason_breakdown(con: duckdb.DuckDBPyConnection):
    return con.execute(
        """
        SELECT
            lost_reason,
            COUNT(*) AS deal_count,
            ROUND(SUM(amount), 2) AS total_amount,
            ROUND(COUNT(*) * 1.0 / SUM(COUNT(*)) OVER (), 4) AS pct_of_losses
        FROM opportunities
        WHERE stage = 'Closed Lost'
        GROUP BY 1
        ORDER BY deal_count DESC
        """
    ).df()


def pipeline_by_segment(con: duckdb.DuckDBPyConnection, dimension: str):
    """dimension must be 'industry', 'region', or 'employee_band' -- validated against this allowlist by the caller (the API layer)."""
    if dimension not in ("industry", "region", "employee_band"):
        raise ValueError("dimension must be 'industry', 'region', or 'employee_band'")
    return con.execute(
        f"""
        SELECT
            a.{dimension} AS segment,
            COUNT(*) AS open_deal_count,
            ROUND(SUM(o.amount), 2) AS open_pipeline_value
        FROM opportunities o
        JOIN accounts a ON a.account_id = o.account_id
        WHERE o.status = 'Open'
        GROUP BY 1
        ORDER BY open_pipeline_value DESC
        """
    ).df()

"""
Deterministic synthetic CRM/GTM data generator for the Revenue & GTM
Operations Intelligence project. Running this script with the fixed SEED
in constants.py always produces byte-identical CSV output -- verified by
tests/test_generator.py.

Simulates a B2B sales pipeline: accounts, sales reps, and opportunities
that progress stage-by-stage (Prospecting -> Qualification -> Proposal ->
Negotiation -> Closed Won/Lost) with stage-conditional advance
probabilities and dwell-time distributions, segment-based territory
assignment, and lead-source quality that actually drives win rate -- the
generator's ground truth that the dashboard's Lead Source view exists to
recover from the data. See constants.py and docs/DATA_DICTIONARY.md.

Output: generator/data/raw/*.csv
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from constants import (
    SEED,
    CREATED_WINDOW_START,
    CREATED_WINDOW_END,
    TODAY,
    N_ACCOUNTS,
    N_REPS,
    N_OPPORTUNITIES,
    TEAMS,
    INDUSTRIES,
    EMPLOYEE_BANDS,
    REGIONS,
    LEAD_SOURCES,
    LEAD_SOURCE_WEIGHTS,
    LEAD_SOURCE_QUALITY,
    LEAD_SOURCE_MISSING_RATE,
    OPEN_STAGES,
    STAGE_ADVANCE_PROB,
    STAGE_DWELL_DAYS,
    STAGE_FORECAST_CATEGORY,
    LOST_REASONS,
    LOST_REASON_WEIGHTS,
    DEAL_AMOUNT_LOGNORMAL_MEAN,
    DEAL_AMOUNT_LOGNORMAL_SIGMA,
    EXPECTED_CYCLE_GAMMA,
    REP_QUOTA_MONTHLY_MIN,
    REP_QUOTA_MONTHLY_MAX,
    BAND_TEAM_WEIGHTS,
)

OUT_DIR = Path(__file__).resolve().parent / "data" / "raw"

COMPANY_WORDS_A = [
    "Acme", "Northfield", "Blue Harbor", "Silver Oak", "Crestview", "Vertex",
    "Ironwood", "Lakeside", "Summit", "Red River", "Granite", "Cedar Point",
    "Falcon", "Meridian", "Harborview", "Union", "Pinecrest", "Horizon",
    "Cobalt", "Maple Grove", "Stonebridge", "Westfield", "Amberline",
]
COMPANY_WORDS_B = [
    "Industries", "Logistics", "Manufacturing", "Trading", "Holdings",
    "Supply Co.", "Distribution", "Enterprises", "Technologies", "Systems",
    "Materials", "Partners", "Group", "Solutions", "Networks",
]
COMPANY_SUFFIX = ["Ltd.", "Inc.", "LLC", "Corp.", "Co.", "& Sons", "International"]

FIRST_NAMES = [
    "Avery", "Jordan", "Priya", "Marcus", "Elena", "Noah", "Fatima", "Lucas",
    "Sofia", "Daniel", "Maya", "Ethan", "Chloe", "Rohan", "Grace", "Tyler",
    "Amara", "Owen", "Nadia", "Caleb",
]
LAST_NAMES = [
    "Chen", "Okafor", "Martinez", "Patel", "Nguyen", "Larsson", "Osei",
    "Kowalski", "Fontaine", "Suzuki", "Haddad", "Romero", "Dubois", "Singh",
    "Mbeki", "Petrov", "Alvarez", "Kim", "Nakamura", "Costa",
]


def company_name(rng: np.random.Generator) -> str:
    a = COMPANY_WORDS_A[rng.integers(0, len(COMPANY_WORDS_A))]
    b = COMPANY_WORDS_B[rng.integers(0, len(COMPANY_WORDS_B))]
    suffix = COMPANY_SUFFIX[rng.integers(0, len(COMPANY_SUFFIX))]
    return f"{a} {b} {suffix}"


def person_name(rng: np.random.Generator) -> str:
    first = FIRST_NAMES[rng.integers(0, len(FIRST_NAMES))]
    last = LAST_NAMES[rng.integers(0, len(LAST_NAMES))]
    return f"{first} {last}"


def weighted_choice(rng: np.random.Generator, options: list, weights: list):
    return options[rng.choice(len(options), p=np.array(weights) / sum(weights))]


@dataclass
class GeneratedData:
    sales_reps: pd.DataFrame
    accounts: pd.DataFrame
    opportunities: pd.DataFrame
    stage_history: pd.DataFrame


def generate_sales_reps(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for i in range(1, N_REPS + 1):
        team = TEAMS[rng.integers(0, len(TEAMS))]
        hire_date = CREATED_WINDOW_START - timedelta(days=int(rng.integers(30, 1500)))
        rows.append({
            "rep_id": f"REP-{i:03d}",
            "name": person_name(rng),
            "team": team,
            "hire_date": hire_date,
            "quota_monthly": int(rng.integers(REP_QUOTA_MONTHLY_MIN, REP_QUOTA_MONTHLY_MAX + 1, dtype=np.int64) // 1000 * 1000),
        })
    return pd.DataFrame(rows)


def generate_accounts(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for i in range(1, N_ACCOUNTS + 1):
        rows.append({
            "account_id": f"ACCT-{i:05d}",
            "name": company_name(rng),
            "industry": INDUSTRIES[rng.integers(0, len(INDUSTRIES))],
            "employee_band": EMPLOYEE_BANDS[rng.integers(0, len(EMPLOYEE_BANDS))],
            "region": REGIONS[rng.integers(0, len(REGIONS))],
            "created_date": CREATED_WINDOW_START - timedelta(days=int(rng.integers(0, 900))),
        })
    return pd.DataFrame(rows)


def pick_rep_for_account(employee_band: str, reps_by_team: dict, rng: np.random.Generator) -> str:
    team_weights = BAND_TEAM_WEIGHTS[employee_band]
    teams = list(team_weights.keys())
    weights = np.array([team_weights[t] for t in teams], dtype=float)
    team = teams[rng.choice(len(teams), p=weights / weights.sum())]
    reps = reps_by_team[team]
    return reps[rng.integers(0, len(reps))]


def sample_created_date(rng: np.random.Generator) -> date:
    """Deal creation volume ramps up over the window (a growing GTM org), not uniform."""
    span_days = (CREATED_WINDOW_END - CREATED_WINDOW_START).days
    # Triangular-shaped draw with density rising toward the end of the
    # window (growing GTM org): for u ~ Uniform(0,1), x = sqrt(u) has a
    # density proportional to x itself, i.e. linearly increasing.
    u = rng.random()
    day_offset = int(span_days * np.sqrt(u))
    return CREATED_WINDOW_START + timedelta(days=day_offset)


def simulate_deal(created_date: date, quality: float, rng: np.random.Generator):
    """
    Walks one opportunity through the pipeline. Returns (stage_history,
    final_stage, status, closed_date, lost_reason). An opportunity still
    short of its next transition as of TODAY is left "Open" in whatever
    stage it last reached -- that censoring is what produces a realistic
    open pipeline alongside the closed historical deals.
    """
    history = [("Prospecting", datetime.combine(created_date, datetime.min.time()))]
    current_dt = datetime.combine(created_date, datetime.min.time())

    for i, stage in enumerate(OPEN_STAGES):
        shape, scale = STAGE_DWELL_DAYS[stage]
        dwell_days = float(rng.gamma(shape, scale))
        transition_dt = current_dt + timedelta(days=dwell_days)

        if transition_dt.date() > TODAY:
            return history, stage, "Open", None, None

        p_advance = min(0.95, STAGE_ADVANCE_PROB[stage] * quality)
        if rng.random() < p_advance:
            if i + 1 < len(OPEN_STAGES):
                next_stage = OPEN_STAGES[i + 1]
                history.append((next_stage, transition_dt))
                current_dt = transition_dt
                continue
            history.append(("Closed Won", transition_dt))
            return history, "Closed Won", "Closed", transition_dt, None

        lost_reason = weighted_choice(rng, LOST_REASONS, LOST_REASON_WEIGHTS)
        history.append(("Closed Lost", transition_dt))
        return history, "Closed Lost", "Closed", transition_dt, lost_reason

    raise AssertionError("unreachable: Negotiation always resolves to Closed Won or Closed Lost")


def generate_opportunities(
    rng: np.random.Generator, accounts: pd.DataFrame, sales_reps: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    reps_by_team = {team: sales_reps.loc[sales_reps.team == team, "rep_id"].tolist() for team in TEAMS}
    account_rows = accounts.to_dict("records")

    opp_rows = []
    history_rows = []

    for i in range(1, N_OPPORTUNITIES + 1):
        account = account_rows[rng.integers(0, len(account_rows))]
        owner_id = pick_rep_for_account(account["employee_band"], reps_by_team, rng)

        has_lead_source = rng.random() >= LEAD_SOURCE_MISSING_RATE
        lead_source = weighted_choice(rng, LEAD_SOURCES, LEAD_SOURCE_WEIGHTS) if has_lead_source else None
        quality = LEAD_SOURCE_QUALITY.get(lead_source, 1.0)

        created_date = sample_created_date(rng)
        history, final_stage, status, closed_dt, lost_reason = simulate_deal(created_date, quality, rng)

        shape, scale = EXPECTED_CYCLE_GAMMA
        expected_close_date = created_date + timedelta(days=float(rng.gamma(shape, scale)))

        amount = round(float(rng.lognormal(DEAL_AMOUNT_LOGNORMAL_MEAN, DEAL_AMOUNT_LOGNORMAL_SIGMA)), 2)
        forecast_category = "Closed Won" if final_stage == "Closed Won" else "Closed Lost" if final_stage == "Closed Lost" else STAGE_FORECAST_CATEGORY[final_stage]

        opp_id = f"OPP-{i:06d}"
        opp_rows.append({
            "opp_id": opp_id,
            "account_id": account["account_id"],
            "owner_id": owner_id,
            "lead_source": lead_source,
            "amount": amount,
            "created_date": created_date,
            "expected_close_date": expected_close_date,
            "status": status,
            "stage": final_stage,
            "forecast_category": forecast_category,
            "closed_date": closed_dt.date() if closed_dt else None,
            "lost_reason": lost_reason,
        })
        for stage_name, entered_at in history:
            history_rows.append({"opp_id": opp_id, "stage": stage_name, "entered_at": entered_at})

    return pd.DataFrame(opp_rows), pd.DataFrame(history_rows)


def generate_all(seed: int = SEED) -> GeneratedData:
    rng = np.random.default_rng(seed)
    sales_reps = generate_sales_reps(rng)
    accounts = generate_accounts(rng)
    opportunities, stage_history = generate_opportunities(rng, accounts, sales_reps)
    return GeneratedData(
        sales_reps=sales_reps,
        accounts=accounts,
        opportunities=opportunities,
        stage_history=stage_history,
    )


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data = generate_all()
    for name in ("sales_reps", "accounts", "opportunities", "stage_history"):
        df = getattr(data, name)
        df.to_csv(OUT_DIR / f"{name}.csv", index=False)
        print(f"{name:16s} {len(df):>8,}")
    print(f"\nWritten to {OUT_DIR}")


if __name__ == "__main__":
    main()

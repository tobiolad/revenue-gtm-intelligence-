"""
Shared constants for the synthetic CRM/GTM data generator. Centralized here
so docs/DATA_DICTIONARY.md and docs/METRIC_DEFINITIONS.md describe the SAME
values the generator actually uses -- not a separately maintained
description that can drift.
"""
from datetime import date

SEED = 19

CREATED_WINDOW_START = date(2024, 10, 1)
CREATED_WINDOW_END = date(2026, 6, 30)
TODAY = date(2026, 7, 15)  # data generation cutoff -- deals not yet closed by here are still "open"

N_ACCOUNTS = 600
N_REPS = 18
N_OPPORTUNITIES = 3000

TEAMS = ["Enterprise", "Mid-Market", "SMB"]
INDUSTRIES = ["SaaS", "Fintech", "Healthcare", "Retail", "Manufacturing", "Education", "Logistics"]
EMPLOYEE_BANDS = ["1-50", "51-200", "201-1000", "1000+"]
REGIONS = ["North America", "EMEA", "APAC", "LATAM"]

LEAD_SOURCES = ["Outbound", "Inbound", "Referral", "Partner", "Event"]
LEAD_SOURCE_WEIGHTS = [0.35, 0.30, 0.15, 0.10, 0.10]
# Relative quality multiplier on every stage-advance probability. >1 =
# better-converting source, <1 = worse. The generator's ground truth --
# the whole point of the Lead Source view is to recover this ranking from
# the data. Same device as CHANNEL_QUALITY in the companion Product
# Analytics Lab project.
LEAD_SOURCE_QUALITY = {
    "Outbound": 0.85,
    "Inbound": 1.10,
    "Referral": 1.35,
    "Partner": 1.15,
    "Event": 0.90,
}
LEAD_SOURCE_MISSING_RATE = 0.02  # fraction of opportunities with no recorded lead_source (CRM data-entry gap)

# Ordered pipeline stages. An opportunity enters at Prospecting and either
# advances through each stage in order or is marked Closed Lost at
# whichever stage it fails to advance from -- see generate.py::simulate_deal.
OPEN_STAGES = ["Prospecting", "Qualification", "Proposal", "Negotiation"]
CLOSED_STAGES = ["Closed Won", "Closed Lost"]
ALL_STAGES = OPEN_STAGES + CLOSED_STAGES

# Base probability (before lead-source quality scaling) of advancing past
# this stage rather than being marked Closed Lost here.
STAGE_ADVANCE_PROB = {
    "Prospecting": 0.70,
    "Qualification": 0.68,
    "Proposal": 0.65,
    "Negotiation": 0.62,
}
# (gamma shape, gamma scale) in days -- how long a deal typically dwells in
# this stage before its next transition (advance or loss).
STAGE_DWELL_DAYS = {
    "Prospecting": (2.0, 6.0),
    "Qualification": (2.0, 8.0),
    "Proposal": (2.5, 10.0),
    "Negotiation": (2.0, 9.0),
}

# Forecast category for an OPEN deal, by current stage -- mirrors standard
# CRM forecast-roll-up categories. Closed deals aren't forecast categories.
STAGE_FORECAST_CATEGORY = {
    "Prospecting": "Pipeline",
    "Qualification": "Pipeline",
    "Proposal": "Best Case",
    "Negotiation": "Commit",
}

LOST_REASONS = ["Budget", "Competitor", "No Decision", "Timing", "Price"]
LOST_REASON_WEIGHTS = [0.28, 0.22, 0.20, 0.18, 0.12]

DEAL_AMOUNT_LOGNORMAL_MEAN = 9.5   # ~$13k median before industry scaling
DEAL_AMOUNT_LOGNORMAL_SIGMA = 0.7

# The rep's target close date, set at creation time and independent of how
# the deal actually plays out -- exactly how a real CRM's close_date field
# works (an estimate made up front, not a fact derived after the close).
# (gamma shape, scale) in days from created_date; mean ~75 days.
EXPECTED_CYCLE_GAMMA = (3.0, 25.0)

REP_QUOTA_MONTHLY_MIN = 35_000
REP_QUOTA_MONTHLY_MAX = 85_000

# Segment-based territory assignment: which team an account's deals are
# worked by, by employee headcount band. Lets "win rate by team" and "rep
# performance by segment" be meaningful cross-cuts instead of arbitrary.
BAND_TEAM_WEIGHTS = {
    "1-50": {"SMB": 0.80, "Mid-Market": 0.20, "Enterprise": 0.00},
    "51-200": {"SMB": 0.50, "Mid-Market": 0.45, "Enterprise": 0.05},
    "201-1000": {"SMB": 0.05, "Mid-Market": 0.65, "Enterprise": 0.30},
    "1000+": {"SMB": 0.00, "Mid-Market": 0.25, "Enterprise": 0.75},
}

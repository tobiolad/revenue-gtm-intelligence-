# Metric definitions

Every metric here has exactly one implementation, in `db/metrics.py`,
tested against a hand-crafted fixture in `tests/test_metrics.py`. This
document is the prose explanation of those same queries -- if the two
ever disagree, the code is correct and this document is stale. Forecast
metrics are documented separately in `docs/FORECAST_METHODOLOGY.md`.

## Bookings trend (`bookings_trend`)

Sum of `amount` for Closed Won deals, bucketed by month or week of
`closed_date`, plus the count of deals won. No denominator -- a raw total.

## Pipeline overview (`pipeline_overview`)

Headline open-pipeline numbers: total count and value of every `status =
'Open'` deal, plus the same broken out by `forecast_category`. Unweighted
-- see `docs/FORECAST_METHODOLOGY.md` for the probability-weighted version.

## Stage funnel (`stage_funnel`)

For each stage in order (Prospecting → Qualification → Proposal →
Negotiation → Closed Won, plus Closed Lost):

- `pct_of_total` -- this stage's count ÷ **all opportunities ever
  created** (a constant denominator across every stage, not the previous
  stage's count).
- `pct_of_previous_stage` -- this stage's count ÷ the **previous open
  stage's** count, for classic funnel drop-off reading. **`Closed Lost`
  has no value here**: losses branch off from every stage, not only from
  Negotiation, so its count is an aggregate across every branch point, not
  one sequential transition -- dividing it by Negotiation's count would
  produce a number over 100% that looks like a bug but isn't a drop-off at
  all. `Closed Won` keeps a real ratio (of Negotiation), since winning
  only happens by advancing out of Negotiation.

## Win rate (`win_rate`, `win_rate_by_lead_source`, `win_rate_by_team`)

Closed Won ÷ (Closed Won + Closed Lost). **Open deals are excluded** --
they haven't resolved yet, and including them (as a loss, or by ignoring
them) would either understate or silently redefine the metric.

## Sales cycle length (`sales_cycle_length`)

Median/mean days from `created_date` to `closed_date`, for Closed Won and
Closed Lost **computed separately**. Lost deals in this dataset resolve on
a visibly shorter timeline than won ones (a prospect saying no is often
faster than a full evaluation cycle ending in a signed deal) -- averaging
the two together would misrepresent both.

## Rep leaderboard (`rep_leaderboard`)

Per-rep bookings, deal count, win rate, and quota attainment over a
trailing window (`trailing_days`, default 365). The "as of" date is the
**latest `closed_date` in the data**, not wall-clock today, so the metric
stays meaningful regardless of how old the dataset is. Quota target for
the window is `quota_monthly * trailing_days / 30` (a 365-day window
implies an annualized quota of `quota_monthly * 12.17`).

## Lost reason breakdown (`lost_reason_breakdown`)

Count, total deal value, and share of all losses, grouped by
`lost_reason`, for Closed Lost deals only.

## Pipeline by segment (`pipeline_by_segment`)

Open pipeline count and value grouped by one of `industry`, `region`, or
`employee_band` (validated against this fixed allowlist before being used
to build SQL -- see the function's docstring in `db/metrics.py`).

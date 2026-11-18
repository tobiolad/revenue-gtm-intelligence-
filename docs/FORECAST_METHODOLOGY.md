# Forecast methodology

Every number here has exactly one implementation, in `db/forecast.py`,
tested against a hand-crafted fixture in `tests/test_forecast.py`. This
document explains what the forecast does, why it's built the way it is,
and -- just as importantly -- what its backtest actually shows, including
where it's wrong.

## The modeling trap this is built to avoid

The pipeline in this dataset is **strictly sequential**: a deal can only
reach Closed Won by advancing out of Negotiation. That means "the
historical win rate of deals whose *final* stage was Prospecting" is 0% by
construction -- not because early-stage deals never win, but because any
deal that wins necessarily passed through every later stage too, so its
*final* stage is never an early one. Using that number as a forecast
weight would zero out two-thirds of the open pipeline's value for no
real reason.

The fix: **win rate conditional on ever having *reached* a stage**, not on
a deal's final stage. For each stage, among CLOSED deals that passed
through it at some point, what fraction eventually won
(`historical_win_rate_by_stage`)? This is well-behaved -- it equals the
overall win rate at Prospecting (since virtually every deal reaches it)
and rises monotonically toward Negotiation, which is exactly the shape a
forecast weighting should have.

## Weighted forecast

Two views, both using the same per-stage weights:

- **`weighted_open_pipeline`** -- a single current snapshot: every open
  deal's amount × the win rate for its *current* stage, summed.
- **`weighted_pipeline_forecast`** -- the same weighting, bucketed by the
  month of each deal's `expected_close_date` (the rep's own target, set at
  creation) -- "what does the pipeline say we'll book, by month, if
  history repeats."

Both are always less than the raw (unweighted) pipeline value, since a win
rate is a fraction in [0, 1].

## The backtest

A forecast that's never checked against reality is just an assertion.
`forecast_accuracy_backtest` reconstructs, for every **fully-elapsed**
calendar month in the data, what the weighted forecast *would have said*
on day 1 of that month:

1. Only deals that **already existed** (created before that day) and were
   **still open** at that moment count as candidates.
2. Each candidate's weight uses its stage **as of that snapshot date**
   (reconstructed from `stage_history`, not its eventual final stage) --
   this is a true point-in-time backtest, not one that peeks at outcomes.
3. Candidates are summed if their `expected_close_date` falls in that
   month, and compared to **actual** Closed-Won bookings for that month.

A month with zero actual bookings **and** zero visible candidates (e.g.
the very first month in the data, before any deal yet existed a full day
in advance) is recorded but excluded from the scored average -- a 0-vs-0
month contributes no information either way.

## What the backtest actually found

Run against the generated dataset, the backtest's overall MAPE (mean
absolute percentage error) is **~37%**, and the forecast is **not
unbiased**: it systematically *under-predicts* almost every month. This
isn't a bug in the backtest -- it's a real, explainable limitation of the
forecast design: the weighting only ever sees deals that were **already
in the pipeline** at the start of the month. It structurally cannot
account for a deal that gets **created and closed within the same month**
-- and because deal volume is growing over the window (a growing GTM
org), that same-month-close effect gets larger, not smaller, as the
dataset progresses. A forecast built this way will always lag a pipeline
that's accelerating.

This is reported plainly, with the number and the reason, rather than
tuned away or hidden -- a forecast's honest error rate is part of what
makes it trustworthy, not something to optimize out of the demo.

## What this forecast deliberately does not do

- No seasonality adjustment, no regression on deal attributes beyond
  stage, no rep-level or segment-level recalibration of the weights --
  one global win-rate-by-stage curve is used everywhere.
- No correction for the same-month-close bias described above; the
  backtest exists to surface it, not paper over it.
- No confidence intervals on the weighted forecast -- it is a point
  estimate, and the backtest's MAPE is the only evidence offered for how
  much to trust it.

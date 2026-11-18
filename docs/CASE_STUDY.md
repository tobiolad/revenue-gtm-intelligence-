# Case study: Revenue & GTM Operations Intelligence

## The problem this demonstrates

Most portfolio "sales dashboards" plot a funnel and a leaderboard and
stop there. This project instead builds what a real revenue operations
team actually needs: a reconstructable pipeline model, metrics with one
documented definition each, and -- the centerpiece -- a probability-
weighted forecast that is **backtested against real historical outcomes**
and reports its own error honestly, including a systematic bias it does
not hide.

**All data is synthetic**, generated deterministically from a fixed seed
-- see `generator/generate.py` and `docs/DATA_DICTIONARY.md`. No real CRM,
customer, or sales data is used anywhere. Numbers quoted below are the
live output of that generator and reproduce exactly with `SEED = 19`.

## What was built

- A deterministic synthetic CRM generator: 18 reps across 3 teams, 600
  accounts, and 3,000 opportunities that progress through a strictly
  sequential pipeline (Prospecting → Qualification → Proposal →
  Negotiation → Closed Won/Lost) with stage-conditional advance
  probabilities, a rep's own independent close-date estimate, and
  lead-source quality that actually drives win rate -- the generator's
  ground truth that the Pipeline Funnel page exists to recover from the
  data, not assert.
- A metrics layer (`db/metrics.py`) covering bookings trend, stage
  funnel, win rate (overall / by source / by team), sales cycle length,
  rep leaderboard with quota attainment, and lost-reason breakdown.
- A forecasting engine (`db/forecast.py`) that derives win rate per
  pipeline stage from historical outcomes -- correcting for a real
  modeling trap where a naive "win rate of a deal's final stage" is 0% for
  every stage but one, by construction (see
  `docs/FORECAST_METHODOLOGY.md`) -- uses it to weight the open pipeline,
  and **backtests that exact weighting against actual past bookings**.
- A FastAPI read-only analytics API and a React + TypeScript dashboard
  (Revenue Overview, Pipeline Funnel, Forecast, Rep Performance, Deals &
  Lost Reasons) with light/dark themes and a validated colorblind-safe
  chart palette, consistent with this portfolio's other data projects.
- 74 automated tests across the generator, metrics, forecast engine, API,
  and frontend -- including a hand-crafted 9-deal fixture with
  known-by-construction correct answers for every metric and every
  forecast calculation, down to the exact dollar.

## What the data actually shows

From one run of the generator (reproducible with `SEED = 19`):

- **22.9% overall win rate** (628 Closed Won, 2,116 Closed Lost), with a
  dramatic, realistic spread by lead source: **Referral leads close at
  58.5%**, versus **Outbound at just 9.3%** -- a 6x difference the
  dashboard surfaces, not asserts.
- Median sales cycle is **65 days for won deals**, versus just **24 days**
  for lost ones -- losing fast, winning slow, exactly the shape a real
  B2B pipeline has.
- The open pipeline is worth **$4.4M raw**, across 256 deals. Weighted by
  each deal's stage-specific historical win rate, that becomes a
  **$2.1M forecast** -- less than half the raw number, which is the point:
  most open pipeline never closes.
- **The backtest is the honest part.** Scored against 20 of 21
  fully-elapsed months, the stage-weighted forecast has an overall MAPE of
  **36.7%**, and it is not unbiased: it systematically *under-predicts*,
  because the weighting can only see deals that already existed at the
  start of each month, and structurally misses deals created and closed
  within the same month -- a miss that grows as the pipeline's own
  creation volume accelerates. This is reported as a finding, not
  smoothed over.

## Engineering decisions worth calling out

- **"Win rate of deals that ever reached a stage," not "win rate of
  deals whose final stage was X."** In a strictly sequential funnel, the
  second definition is a tautology (0% for every non-terminal stage) --
  catching this before it silently zeroed out the forecast was the single
  most important modeling decision in this project; see
  `docs/FORECAST_METHODOLOGY.md` for the full explanation.
- **A true point-in-time backtest, not a convenient approximation.** The
  backtest reconstructs each deal's pipeline stage *as it stood on the
  snapshot date* from `stage_history`, rather than reading each deal's
  eventual outcome -- the difference between genuinely testing a forecast
  and quietly cheating with hindsight.
- **`expected_close_date` is independent of outcome.** It's generated at
  deal-creation time from its own random draw, with no knowledge of how
  the deal will actually resolve -- exactly how a rep's estimate works in
  a real CRM, and the only way a forecast backtest against it means
  anything.
- **One metric definition, three consumers.** Every number the dashboard
  shows, the API serves, and the test suite checks traces back to the
  same function in `db/metrics.py` or `db/forecast.py` -- no second,
  hand-maintained copy of "how do we compute win rate" anywhere.

## Honest limitations

- Synthetic pipeline dynamics (stage-conditional probabilities, gamma
  dwell times) are a plausible model of a B2B sales process, not a
  validated one against any real company's data.
- The forecast uses a single global win-rate-by-stage curve; it does not
  recalibrate per segment, per rep, or per deal size, all of which a
  production forecasting model typically would.
- The backtest's systematic under-prediction is diagnosed but not
  corrected -- a production version of this tool would need a second
  weighting term for "deals not yet created," which this project
  deliberately leaves as a documented gap rather than a hidden one.

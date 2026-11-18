-- Revenue & GTM Operations Intelligence — schema
--
-- stage_history is event-sourced: one row per (opportunity, pipeline stage
-- actually reached), in order. opportunities.stage is the CURRENT/FINAL
-- stage as a convenience column for simple lookups; every funnel,
-- conversion, and cycle-time query reads stage_history instead, the same
-- discipline as onboarding_progress in the companion Product Analytics
-- Lab project.

CREATE TABLE sales_reps (
    rep_id         VARCHAR PRIMARY KEY,
    name           VARCHAR NOT NULL,
    team           VARCHAR NOT NULL,  -- Enterprise | Mid-Market | SMB
    hire_date      DATE NOT NULL,
    quota_monthly  DOUBLE NOT NULL
);

CREATE TABLE accounts (
    account_id     VARCHAR PRIMARY KEY,
    name           VARCHAR NOT NULL,
    industry       VARCHAR NOT NULL,
    employee_band  VARCHAR NOT NULL,
    region         VARCHAR NOT NULL,
    created_date   DATE NOT NULL
);

CREATE TABLE opportunities (
    opp_id              VARCHAR PRIMARY KEY,
    account_id          VARCHAR NOT NULL REFERENCES accounts(account_id),
    owner_id            VARCHAR NOT NULL REFERENCES sales_reps(rep_id),
    lead_source         VARCHAR,  -- nullable: ~2% of deals have no recorded source (CRM data-entry gap)
    amount              DOUBLE NOT NULL,
    created_date        DATE NOT NULL,
    expected_close_date DATE NOT NULL,  -- the rep's target close date, set at creation, independent of the actual outcome
    status              VARCHAR NOT NULL,  -- 'Open' | 'Closed'
    stage               VARCHAR NOT NULL,  -- current (if Open) or final (if Closed) stage
    forecast_category   VARCHAR NOT NULL,  -- Pipeline | Best Case | Commit | Closed Won | Closed Lost
    closed_date         DATE,              -- nullable: only set once status = 'Closed'
    lost_reason          VARCHAR           -- nullable: only set when stage = 'Closed Lost'
);

-- NOT deduplicated by design -- an opportunity may re-enter a stage in a
-- real CRM (e.g. bounced back from Negotiation to Proposal); this
-- generator doesn't model that, but the schema doesn't assume uniqueness.
CREATE TABLE stage_history (
    opp_id      VARCHAR NOT NULL REFERENCES opportunities(opp_id),
    stage       VARCHAR NOT NULL,
    entered_at  TIMESTAMP NOT NULL
);

-- Canonical, reused derived view. Every funnel-conversion and
-- cycle-time query reads from `stage_progress` rather than re-deriving
-- the join to opportunities and the days-since-created calculation --
-- a single, auditable definition, the same discipline as
-- onboarding_progress in the companion Product Analytics Lab project.
CREATE OR REPLACE VIEW stage_progress AS
SELECT
    sh.opp_id,
    sh.stage,
    sh.entered_at,
    o.created_date,
    o.owner_id,
    o.lead_source,
    date_diff('day', o.created_date, CAST(sh.entered_at AS DATE)) AS days_since_created
FROM stage_history sh
JOIN opportunities o ON o.opp_id = sh.opp_id;

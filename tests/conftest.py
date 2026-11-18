import sys
from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generator"))
sys.path.insert(0, str(ROOT / "db"))

SQL_DIR = ROOT / "db" / "sql"


@pytest.fixture
def con():
    """
    A small, hand-crafted pipeline where the correct answer to every
    metric/forecast query is known in advance -- not a sample of the
    generated data, which would make the test circular.

    sales_reps: REP-1 (SMB, quota 10000/mo), REP-2 (Enterprise, quota 20000/mo)
    accounts:   ACCT-1 (REP-1's account), ACCT-2 (REP-2's account)

    Opportunities (all owned per the account above):
      OPP-1  Referral  $10,000  created 2026-01-01  Prospecting->Qualification->Proposal->Negotiation->Closed Won (2026-01-15)
      OPP-2  Referral  $5,000   created 2026-01-01  Prospecting->Qualification->Closed Lost (2026-01-10, 'Price')
      OPP-3  Outbound  $20,000  created 2026-01-01  Prospecting->Closed Lost (2026-01-05, 'Budget')
      OPP-4  Outbound  $15,000  created 2026-01-01  Prospecting->Qualification->Proposal->Negotiation->Closed Won (2026-02-05)
      OPP-5  (none)    $8,000   created 2026-01-10  Prospecting->Qualification->Proposal; still OPEN, expected close 2026-02-15
      OPP-6  Outbound  $12,000  created 2026-01-05  Prospecting->Qualification; still OPEN, expected close 2026-02-20
      OPP-7  Referral  $9,000   created 2026-01-12  Prospecting only; still OPEN, expected close 2026-03-01
      OPP-8  Outbound  $25,000  created 2026-01-02  Prospecting->Qualification->Proposal->Negotiation; still OPEN, expected close 2026-02-10
      OPP-9  Referral  $16,000  created 2025-12-01  Prospecting (12-01) ->Qualification (12-10); still OPEN, expected close 2026-01-20
           -- the only deal created before 2026-01-01, so the only candidate
              the forecast backtest can "see" as of a 2026-01-01 snapshot.

    Only OPP-1 and OPP-4 ever reach Negotiation and win -- by construction
    of a strictly sequential funnel, winning is only possible by advancing
    out of Negotiation, which is exactly the modeling fact
    historical_win_rate_by_stage exists to handle correctly (see
    db/forecast.py's docstring).
    """
    c = duckdb.connect(":memory:")
    c.execute((SQL_DIR / "001_schema.sql").read_text())

    c.execute(
        """
        INSERT INTO sales_reps VALUES
            ('REP-1', 'Alex Kim', 'SMB', '2023-01-01', 10000),
            ('REP-2', 'Sam Lee', 'Enterprise', '2023-01-01', 20000)
        """
    )
    c.execute(
        """
        INSERT INTO accounts VALUES
            ('ACCT-1', 'Acme Industries Ltd.', 'SaaS', '1-50', 'North America', '2024-01-01'),
            ('ACCT-2', 'Vertex Holdings Inc.', 'Fintech', '1000+', 'North America', '2024-01-01')
        """
    )
    c.execute(
        """
        INSERT INTO opportunities VALUES
            ('OPP-1', 'ACCT-1', 'REP-1', 'Referral', 10000, '2026-01-01', '2026-01-20', 'Closed', 'Closed Won', 'Closed Won', '2026-01-15', NULL),
            ('OPP-2', 'ACCT-1', 'REP-1', 'Referral', 5000,  '2026-01-01', '2026-01-15', 'Closed', 'Closed Lost', 'Closed Lost', '2026-01-10', 'Price'),
            ('OPP-3', 'ACCT-2', 'REP-2', 'Outbound', 20000, '2026-01-01', '2026-01-10', 'Closed', 'Closed Lost', 'Closed Lost', '2026-01-05', 'Budget'),
            ('OPP-4', 'ACCT-2', 'REP-2', 'Outbound', 15000, '2026-01-01', '2026-02-10', 'Closed', 'Closed Won', 'Closed Won', '2026-02-05', NULL),
            ('OPP-5', 'ACCT-1', 'REP-1', NULL,       8000,  '2026-01-10', '2026-02-15', 'Open',   'Proposal', 'Best Case', NULL, NULL),
            ('OPP-6', 'ACCT-2', 'REP-2', 'Outbound', 12000, '2026-01-05', '2026-02-20', 'Open',   'Qualification', 'Pipeline', NULL, NULL),
            ('OPP-7', 'ACCT-1', 'REP-1', 'Referral', 9000,  '2026-01-12', '2026-03-01', 'Open',   'Prospecting', 'Pipeline', NULL, NULL),
            ('OPP-8', 'ACCT-2', 'REP-2', 'Outbound', 25000, '2026-01-02', '2026-02-10', 'Open',   'Negotiation', 'Commit', NULL, NULL),
            ('OPP-9', 'ACCT-1', 'REP-1', 'Referral', 16000, '2025-12-01', '2026-01-20', 'Open',   'Qualification', 'Pipeline', NULL, NULL)
        """
    )
    c.execute(
        """
        INSERT INTO stage_history VALUES
            ('OPP-1', 'Prospecting', '2026-01-01'), ('OPP-1', 'Qualification', '2026-01-03'), ('OPP-1', 'Proposal', '2026-01-06'), ('OPP-1', 'Negotiation', '2026-01-10'), ('OPP-1', 'Closed Won', '2026-01-15'),
            ('OPP-2', 'Prospecting', '2026-01-01'), ('OPP-2', 'Qualification', '2026-01-04'), ('OPP-2', 'Closed Lost', '2026-01-10'),
            ('OPP-3', 'Prospecting', '2026-01-01'), ('OPP-3', 'Closed Lost', '2026-01-05'),
            ('OPP-4', 'Prospecting', '2026-01-01'), ('OPP-4', 'Qualification', '2026-01-04'), ('OPP-4', 'Proposal', '2026-01-09'), ('OPP-4', 'Negotiation', '2026-01-15'), ('OPP-4', 'Closed Won', '2026-02-05'),
            ('OPP-5', 'Prospecting', '2026-01-10'), ('OPP-5', 'Qualification', '2026-01-13'), ('OPP-5', 'Proposal', '2026-01-18'),
            ('OPP-6', 'Prospecting', '2026-01-05'), ('OPP-6', 'Qualification', '2026-01-08'),
            ('OPP-7', 'Prospecting', '2026-01-12'),
            ('OPP-8', 'Prospecting', '2026-01-02'), ('OPP-8', 'Qualification', '2026-01-06'), ('OPP-8', 'Proposal', '2026-01-11'), ('OPP-8', 'Negotiation', '2026-01-16'),
            ('OPP-9', 'Prospecting', '2025-12-01'), ('OPP-9', 'Qualification', '2025-12-10')
        """
    )

    c.execute((SQL_DIR / "002_views.sql").read_text())
    return c

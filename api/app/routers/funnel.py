from __future__ import annotations

import duckdb
from fastapi import APIRouter, Depends

from ..db import get_connection, metrics
from ..serialize import df_to_records

router = APIRouter(prefix="/funnel", tags=["funnel"])


@router.get("/stages")
def stage_funnel(con: duckdb.DuckDBPyConnection = Depends(get_connection)):
    return df_to_records(metrics.stage_funnel(con))


@router.get("/cycle-length")
def sales_cycle_length(con: duckdb.DuckDBPyConnection = Depends(get_connection)):
    return metrics.sales_cycle_length(con)


@router.get("/win-rate-by-lead-source")
def win_rate_by_lead_source(con: duckdb.DuckDBPyConnection = Depends(get_connection)):
    return df_to_records(metrics.win_rate_by_lead_source(con))


@router.get("/win-rate-by-team")
def win_rate_by_team(con: duckdb.DuckDBPyConnection = Depends(get_connection)):
    return df_to_records(metrics.win_rate_by_team(con))

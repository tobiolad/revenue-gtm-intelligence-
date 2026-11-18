from __future__ import annotations

import duckdb
from fastapi import APIRouter, Depends, Query

from ..db import get_connection, metrics
from ..serialize import df_to_records

router = APIRouter(prefix="/reps", tags=["reps"])


@router.get("/leaderboard")
def rep_leaderboard(
    trailing_days: int = Query(365, ge=1, le=1825),
    con: duckdb.DuckDBPyConnection = Depends(get_connection),
):
    return df_to_records(metrics.rep_leaderboard(con, trailing_days=trailing_days))

from __future__ import annotations

from typing import Literal

import duckdb
from fastapi import APIRouter, Depends

from ..db import get_connection, metrics
from ..serialize import df_to_records

router = APIRouter(prefix="/deals", tags=["deals"])


@router.get("/lost-reasons")
def lost_reason_breakdown(con: duckdb.DuckDBPyConnection = Depends(get_connection)):
    return df_to_records(metrics.lost_reason_breakdown(con))


@router.get("/pipeline-by-segment")
def pipeline_by_segment(
    dimension: Literal["industry", "region", "employee_band"] = "industry",
    con: duckdb.DuckDBPyConnection = Depends(get_connection),
):
    return df_to_records(metrics.pipeline_by_segment(con, dimension))

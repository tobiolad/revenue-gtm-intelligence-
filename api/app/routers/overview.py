from __future__ import annotations

from typing import Literal

import duckdb
from fastapi import APIRouter, Depends

from ..db import get_connection, metrics
from ..serialize import df_to_records

router = APIRouter(prefix="/overview", tags=["overview"])


@router.get("/bookings-trend")
def bookings_trend(
    granularity: Literal["week", "month"] = "month",
    con: duckdb.DuckDBPyConnection = Depends(get_connection),
):
    return df_to_records(metrics.bookings_trend(con, granularity=granularity))


@router.get("/pipeline")
def pipeline_overview(con: duckdb.DuckDBPyConnection = Depends(get_connection)):
    result = metrics.pipeline_overview(con)
    return {
        "open_deal_count": result["open_deal_count"],
        "open_pipeline_value": result["open_pipeline_value"],
        "by_forecast_category": df_to_records(result["by_forecast_category"]),
    }


@router.get("/win-rate")
def win_rate(con: duckdb.DuckDBPyConnection = Depends(get_connection)):
    return metrics.win_rate(con)

from __future__ import annotations

import duckdb
from fastapi import APIRouter, Depends

from ..db import get_connection, forecast
from ..serialize import df_to_records

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.get("/win-rates-by-stage")
def historical_win_rate_by_stage(con: duckdb.DuckDBPyConnection = Depends(get_connection)):
    return df_to_records(forecast.historical_win_rate_by_stage(con))


@router.get("/weighted-pipeline")
def weighted_open_pipeline(con: duckdb.DuckDBPyConnection = Depends(get_connection)):
    return forecast.weighted_open_pipeline(con)


@router.get("/monthly")
def weighted_pipeline_forecast(con: duckdb.DuckDBPyConnection = Depends(get_connection)):
    return df_to_records(forecast.weighted_pipeline_forecast(con))


@router.get("/backtest")
def forecast_accuracy_backtest(con: duckdb.DuckDBPyConnection = Depends(get_connection)):
    result = forecast.forecast_accuracy_backtest(con)
    return {
        "by_month": df_to_records(result["by_month"]),
        "overall_mape": result["overall_mape"],
        "months_scored": result["months_scored"],
        "months_total": result["months_total"],
    }

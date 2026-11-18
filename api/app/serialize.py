"""
DataFrame -> JSON-safe records. Metric/forecast functions return pandas
DataFrames with numpy scalar dtypes, dates and NaNs that FastAPI's default
encoder doesn't handle; round-tripping through pandas' own to_json (which
already knows how to serialize all of those) is simpler and more reliable
than hand-rolling a converter.
"""
from __future__ import annotations

import json

import pandas as pd


def df_to_records(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return []
    return json.loads(df.to_json(orient="records", date_format="iso"))

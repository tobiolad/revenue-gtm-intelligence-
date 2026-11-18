"""
Read-only DuckDB access for the API. Opens the database built by
`db/load.py` in read-only mode so the API can never mutate the analytics
store, and reuses the exact same metric/forecast logic the tests verify
against -- the API is a thin HTTP wrapper, not a second implementation.
"""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = ROOT / "db" / "gtm.duckdb"

sys.path.insert(0, str(ROOT / "db"))

import metrics  # noqa: E402
import forecast  # noqa: E402

__all__ = ["get_connection", "metrics", "forecast", "DB_PATH"]


def get_connection() -> duckdb.DuckDBPyConnection:
    if not DB_PATH.exists():
        raise RuntimeError(
            f"No database found at {DB_PATH}. Run `python generator/generate.py` then `python db/load.py` first."
        )
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        yield con
    finally:
        con.close()

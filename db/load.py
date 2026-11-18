"""
Builds the DuckDB analytical database from the generated CSVs. Reproducible
and idempotent: deletes any existing database file and rebuilds fresh.

Usage:
    python db/load.py
"""
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "generator" / "data" / "raw"
DB_PATH = ROOT / "db" / "gtm.duckdb"
SQL_DIR = Path(__file__).resolve().parent / "sql"

# Explicit (destination columns, source columns) per table -- avoids
# relying on `SELECT *` column order matching the CSV's actual on-disk
# order, which is not guaranteed to match the table DDL's declared order.
TABLES = {
    "sales_reps": "rep_id,name,team,hire_date,quota_monthly",
    "accounts": "account_id,name,industry,employee_band,region,created_date",
    "opportunities": "opp_id,account_id,owner_id,lead_source,amount,created_date,expected_close_date,status,stage,forecast_category,closed_date,lost_reason",
    "stage_history": "opp_id,stage,entered_at",
}


def main():
    if DB_PATH.exists():
        DB_PATH.unlink()

    con = duckdb.connect(str(DB_PATH))
    con.execute((SQL_DIR / "001_schema.sql").read_text())

    for table, cols in TABLES.items():
        csv_path = RAW_DIR / f"{table}.csv"
        con.execute(
            f"INSERT INTO {table} ({cols}) SELECT {cols} FROM read_csv_auto(?, header=True)",
            [str(csv_path)],
        )
        count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table:16s} {count:>8,}")

    con.execute((SQL_DIR / "002_views.sql").read_text())
    con.close()
    print(f"\nBuilt {DB_PATH}")


if __name__ == "__main__":
    main()

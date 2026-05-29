# pipeline/analyse.py
# PURPOSE: Run all SQL analytical queries against the DuckDB database
# and export results as CSVs for Power BI consumption.

import duckdb
import pandas as pd
import os

DB_PATH    = "data/processed/ecommerce.duckdb"
SQL_PATH   = "sql/views"
OUT_PATH   = "data/processed"


def run_query_from_file(conn: duckdb.DuckDBPyConnection,
                        filepath: str) -> pd.DataFrame:
    """
    Read a SQL file and execute it against the database.
    Returns the result as a DataFrame.
    """
    with open(filepath, "r") as f:
        sql = f.read()
    return conn.execute(sql).fetchdf()


def run_all_analyses():
    conn = duckdb.connect(DB_PATH)

    queries = {
        "monthly_revenue":    "01_monthly_revenue.sql",
        "customer_retention": "02_customer_retention.sql",
        "rfm_segments":       "03_rfm_segments.sql",
        "category_performance": "04_category_performance.sql",
    }

    for name, filename in queries.items():
        filepath = os.path.join(SQL_PATH, filename)
        print(f"\n--- Running: {filename} ---")

        df = run_query_from_file(conn, filepath)

        # Save to CSV for Power BI
        out_file = os.path.join(OUT_PATH, f"{name}.csv")
        df.to_csv(out_file, index=False)

        print(f"  Rows returned: {len(df):,}")
        print(f"  Saved to: {out_file}")
        print(df.head(3).to_string(index=False))

    conn.close()
    print("\n=== All analyses complete ===")


if __name__ == "__main__":
    run_all_analyses()
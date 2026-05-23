# pipeline/extract.py
# PURPOSE: Load all raw CSV files and produce a data quality summary.
# This is the EXTRACT step in our ETL pipeline.

import pandas as pd
import os

RAW_DATA_PATH = "data/raw"

FILES = {
    "customers":    "olist_customers_dataset.csv",
    "geolocation":  "olist_geolocation_dataset.csv",
    "order_items":  "olist_order_items_dataset.csv",
    "payments":     "olist_order_payments_dataset.csv",
    "reviews":      "olist_order_reviews_dataset.csv",
    "orders":       "olist_orders_dataset.csv",
    "products":     "olist_products_dataset.csv",
    "sellers":      "olist_sellers_dataset.csv",
    "translations": "product_category_name_translation.csv",
}


def load_all_files(path: str, files: dict) -> dict:
    """
    Load every CSV into a pandas DataFrame.
    Returns a dict like {"customers": df, "orders": df, ...}
    """
    dataframes = {}
    for name, filename in files.items():
        full_path = os.path.join(path, filename)
        df = pd.read_csv(full_path)
        dataframes[name] = df
        print(f"  Loaded '{name}': {df.shape[0]:,} rows x {df.shape[1]} columns")
    return dataframes


def audit_dataframes(dataframes: dict) -> pd.DataFrame:
    """
    For each DataFrame, compute:
      - row count
      - column count
      - total null values
      - null percentage
      - duplicate row count
    """
    summary_rows = []

    for name, df in dataframes.items():
        total_cells = df.shape[0] * df.shape[1]
        null_count  = df.isnull().sum().sum()
        null_pct    = round((null_count / total_cells) * 100, 2)
        dupe_count  = df.duplicated().sum()

        summary_rows.append({
            "table":      name,
            "rows":       df.shape[0],
            "columns":    df.shape[1],
            "nulls":      null_count,
            "null_%":     null_pct,
            "duplicates": dupe_count,
        })

    return pd.DataFrame(summary_rows)


if __name__ == "__main__":
    print("\n=== Loading raw data files ===\n")
    dfs = load_all_files(RAW_DATA_PATH, FILES)

    print("\n=== Data Quality Audit ===\n")
    audit = audit_dataframes(dfs)
    print(audit.to_string(index=False))

    audit.to_csv("data/processed/audit_raw.csv", index=False)
    print("\nAudit saved to data/processed/audit_raw.csv")
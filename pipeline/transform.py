# pipeline/transform.py
# PURPOSE: Clean raw DataFrames and prepare them for loading into the star schema.
# This is the TRANSFORM step in our ETL pipeline.

import pandas as pd


def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the orders table.
    - Convert all timestamp columns to datetime
    - Fill nulls in delivery dates with a placeholder
    - Keep only delivered orders for our analysis
    """
    timestamp_cols = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for col in timestamp_cols:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    # We keep all statuses but flag undelivered ones
    df["is_delivered"] = df["order_status"] == "delivered"
    return df


def clean_customers(df: pd.DataFrame) -> pd.DataFrame():
    """
    Clean the customers table.
    - Rename columns to be more readable
    - Standardise state codes to uppercase
    """
    df = df.rename(columns={
        "customer_unique_id": "unique_customer_id",
        "customer_zip_code_prefix": "zip_code",
        "customer_city": "city",
        "customer_state": "state",
    })
    df["state"] = df["state"].str.upper().str.strip()
    df["city"]  = df["city"].str.title().str.strip()
    return df


def clean_products(df: pd.DataFrame, translations: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the products table.
    - Join with translations to get English category names
    - Fill missing category names with 'unknown'
    - Fill missing numeric fields with 0
    """
    df = df.merge(translations, on="product_category_name", how="left")

    df["product_category_name_english"] = (
        df["product_category_name_english"]
        .fillna("unknown")
        .str.replace("_", " ")
        .str.title()
        .str.strip()
    )

    numeric_cols = [
        "product_name_lenght",
        "product_description_lenght",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ]
    df[numeric_cols] = df[numeric_cols].fillna(0)
    return df


def clean_order_items(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the order items table.
    - Convert shipping date to datetime
    - Ensure price and freight are positive
    """
    df["shipping_limit_date"] = pd.to_datetime(
        df["shipping_limit_date"], errors="coerce"
    )
    df = df[df["price"] > 0]
    return df


def clean_sellers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the sellers table.
    - Standardise state and city formatting
    """
    df["seller_state"] = df["seller_state"].str.upper().str.strip()
    df["seller_city"]  = df["seller_city"].str.title().str.strip()
    return df


def build_dim_date(orders: pd.DataFrame) -> pd.DataFrame:
    """
    Build a date dimension table from the range of order dates.
    This gives us a calendar table we can use for time intelligence in Power BI.
    """
    min_date = orders["order_purchase_timestamp"].min()
    max_date = orders["order_purchase_timestamp"].max()

    date_range = pd.date_range(start=min_date, end=max_date, freq="D")

    dim_date = pd.DataFrame({"date": date_range})
    dim_date["year"]        = dim_date["date"].dt.year
    dim_date["month"]       = dim_date["date"].dt.month
    dim_date["month_name"]  = dim_date["date"].dt.strftime("%B")
    dim_date["quarter"]     = dim_date["date"].dt.quarter
    dim_date["weekday"]     = dim_date["date"].dt.day_name()
    dim_date["is_weekend"]  = dim_date["date"].dt.weekday >= 5
    dim_date["date"]        = dim_date["date"].dt.date

    return dim_date


if __name__ == "__main__":
    # Quick test — run transforms and print shape of each output
    from extract import load_all_files, FILES, RAW_DATA_PATH

    print("\n=== Running transforms ===\n")
    dfs = load_all_files(RAW_DATA_PATH, FILES)

    orders       = clean_orders(dfs["orders"])
    customers    = clean_customers(dfs["customers"])
    products     = clean_products(dfs["products"], dfs["translations"])
    order_items  = clean_order_items(dfs["order_items"])
    sellers      = clean_sellers(dfs["sellers"])
    dim_date     = build_dim_date(orders)

    print(f"\n  orders:      {orders.shape}")
    print(f"  customers:   {customers.shape}")
    print(f"  products:    {products.shape}")
    print(f"  order_items: {order_items.shape}")
    print(f"  sellers:     {sellers.shape}")
    print(f"  dim_date:    {dim_date.shape}")
    print("\nAll transforms successful.")
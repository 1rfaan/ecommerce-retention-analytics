# pipeline/load.py
# PURPOSE: Load all cleaned DataFrames into DuckDB as a star schema.
# This is the LOAD step in our ETL pipeline.

import duckdb
import pandas as pd
import os
import sys

# Add the pipeline folder to path so we can import our other scripts
sys.path.append(os.path.dirname(__file__))

from extract import load_all_files, FILES, RAW_DATA_PATH
from transform import (
    clean_orders,
    clean_customers,
    clean_products,
    clean_order_items,
    clean_sellers,
    build_dim_date,
)

DB_PATH = "data/processed/ecommerce.duckdb"


def build_star_schema(conn: duckdb.DuckDBPyConnection):
    """
    Create all tables in the star schema.
    We drop in reverse dependency order (facts first, then dims)
    so foreign key constraints don't block us.
    """
    # Drop fact tables first (they depend on dims)
    conn.execute("DROP TABLE IF EXISTS fact_order_items")
    conn.execute("DROP TABLE IF EXISTS fact_orders")

    # Then drop dimension tables
    conn.execute("DROP TABLE IF EXISTS dim_customers")
    conn.execute("DROP TABLE IF EXISTS dim_products")
    conn.execute("DROP TABLE IF EXISTS dim_sellers")
    conn.execute("DROP TABLE IF EXISTS dim_date")

    conn.execute("""
        CREATE TABLE dim_customers (
            customer_id         VARCHAR PRIMARY KEY,
            unique_customer_id  VARCHAR,
            zip_code            VARCHAR,
            city                VARCHAR,
            state               VARCHAR
        )
    """)

    conn.execute("""
        CREATE TABLE dim_products (
            product_id       VARCHAR PRIMARY KEY,
            category_english VARCHAR,
            weight_g         FLOAT,
            length_cm        FLOAT,
            height_cm        FLOAT,
            width_cm         FLOAT
        )
    """)

    conn.execute("""
        CREATE TABLE dim_sellers (
            seller_id   VARCHAR PRIMARY KEY,
            zip_code    VARCHAR,
            city        VARCHAR,
            state       VARCHAR
        )
    """)

    conn.execute("""
        CREATE TABLE dim_date (
            date        DATE PRIMARY KEY,
            year        INTEGER,
            month       INTEGER,
            month_name  VARCHAR,
            quarter     INTEGER,
            weekday     VARCHAR,
            is_weekend  BOOLEAN
        )
    """)

    conn.execute("""
        CREATE TABLE fact_orders (
            order_id            VARCHAR PRIMARY KEY,
            customer_id         VARCHAR,
            order_status        VARCHAR,
            purchase_date       DATE,
            purchase_timestamp  TIMESTAMP,
            is_delivered        BOOLEAN,
            FOREIGN KEY (customer_id) REFERENCES dim_customers(customer_id)
        )
    """)

    conn.execute("""
        CREATE TABLE fact_order_items (
            order_id    VARCHAR,
            product_id  VARCHAR,
            seller_id   VARCHAR,
            price       FLOAT,
            freight     FLOAT,
            quantity    INTEGER,
            FOREIGN KEY (order_id)   REFERENCES fact_orders(order_id),
            FOREIGN KEY (product_id) REFERENCES dim_products(product_id),
            FOREIGN KEY (seller_id)  REFERENCES dim_sellers(seller_id)
        )
    """)

    print("  Schema created successfully.")


def load_data(conn: duckdb.DuckDBPyConnection, dfs: dict):
    """
    Load cleaned DataFrames into DuckDB tables.
    DuckDB can read pandas DataFrames directly — no CSV export needed.
    """

    # --- dim_customers ---
    customers = clean_customers(dfs["customers"])
    conn.execute("""
        INSERT INTO dim_customers
        SELECT
            customer_id,
            unique_customer_id,
            zip_code,
            city,
            state
        FROM customers
    """)
    print(f"  dim_customers: {len(customers):,} rows loaded")

    # --- dim_products ---
    products = clean_products(dfs["products"], dfs["translations"])
    conn.execute("""
        INSERT INTO dim_products
        SELECT
            product_id,
            product_category_name_english  AS category_english,
            product_weight_g               AS weight_g,
            product_length_cm              AS length_cm,
            product_height_cm              AS height_cm,
            product_width_cm               AS width_cm
        FROM products
    """)
    print(f"  dim_products:  {len(products):,} rows loaded")

    # --- dim_sellers ---
    sellers = clean_sellers(dfs["sellers"])
    conn.execute("""
        INSERT INTO dim_sellers
        SELECT
            seller_id,
            seller_zip_code_prefix AS zip_code,
            seller_city            AS city,
            seller_state           AS state
        FROM sellers
    """)
    print(f"  dim_sellers:   {len(sellers):,} rows loaded")

    # --- dim_date ---
    orders = clean_orders(dfs["orders"])
    date_df = build_dim_date(orders)
    conn.execute("""
        INSERT INTO dim_date
        SELECT date, year, month, month_name, quarter, weekday, is_weekend
        FROM date_df
    """)
    print(f"  dim_date:      {len(date_df):,} rows loaded")

    # --- fact_orders ---
    conn.execute("""
        INSERT INTO fact_orders
        SELECT
            order_id,
            customer_id,
            order_status,
            CAST(order_purchase_timestamp AS DATE) AS purchase_date,
            order_purchase_timestamp               AS purchase_timestamp,
            is_delivered
        FROM orders
    """)
    print(f"  fact_orders:   {len(orders):,} rows loaded")

    # --- fact_order_items ---
    order_items = clean_order_items(dfs["order_items"])
    conn.execute("""
        INSERT INTO fact_order_items
        SELECT
            order_id,
            product_id,
            seller_id,
            price,
            freight_value AS freight,
            order_item_id AS quantity
        FROM order_items
    """)
    print(f"  fact_order_items: {len(order_items):,} rows loaded")


def verify_load(conn: duckdb.DuckDBPyConnection):
    """
    Run a quick verification query to confirm data loaded correctly.
    """
    result = conn.execute("""
        SELECT
            'fact_orders'      AS table_name, COUNT(*) AS row_count FROM fact_orders
        UNION ALL SELECT 'fact_order_items', COUNT(*) FROM fact_order_items
        UNION ALL SELECT 'dim_customers',    COUNT(*) FROM dim_customers
        UNION ALL SELECT 'dim_products',     COUNT(*) FROM dim_products
        UNION ALL SELECT 'dim_sellers',      COUNT(*) FROM dim_sellers
        UNION ALL SELECT 'dim_date',         COUNT(*) FROM dim_date
    """).fetchdf()
    print("\n=== Database verification ===\n")
    print(result.to_string(index=False))


if __name__ == "__main__":
    print("\n=== Starting ETL load ===\n")

    # Load raw data
    dfs = load_all_files(RAW_DATA_PATH, FILES)

    # Connect to DuckDB (creates the file if it doesn't exist)
    conn = duckdb.connect(DB_PATH)

    print("\n--- Creating schema ---\n")
    build_star_schema(conn)

    print("\n--- Loading data ---\n")
    load_data(conn, dfs)

    verify_load(conn)

    conn.close()
    print("\nDatabase saved to:", DB_PATH)
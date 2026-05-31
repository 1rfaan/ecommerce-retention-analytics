# pipeline/export_powerbi.py
# PURPOSE: Export clean, Power BI ready CSV files from DuckDB.

import duckdb
import pandas as pd

DB_PATH  = "data/processed/ecommerce.duckdb"
OUT_PATH = "data/processed"

conn = duckdb.connect(DB_PATH)

# ── Export 1: Orders with full context ──
print("Exporting orders master...")
orders_master = conn.execute("""
    SELECT
        fo.order_id,
        fo.purchase_date,
        fo.order_status,
        fo.is_delivered,
        dc.unique_customer_id,
        dc.city          AS customer_city,
        dc.state         AS customer_state,
        dd.year,
        dd.month,
        dd.month_name,
        dd.quarter,
        dd.weekday,
        dd.is_weekend,
        SUM(foi.price)   AS revenue,
        SUM(foi.freight) AS freight,
        COUNT(foi.quantity) AS item_count
    FROM fact_orders fo
    JOIN dim_customers dc     ON fo.customer_id   = dc.customer_id
    JOIN dim_date dd          ON fo.purchase_date = dd.date
    JOIN fact_order_items foi ON fo.order_id      = foi.order_id
    WHERE fo.is_delivered = true
    GROUP BY
        fo.order_id, fo.purchase_date, fo.order_status,
        fo.is_delivered, dc.unique_customer_id,
        dc.city, dc.state,
        dd.year, dd.month, dd.month_name,
        dd.quarter, dd.weekday, dd.is_weekend
""").fetchdf()

orders_master.to_csv(f"{OUT_PATH}/orders_master.csv", index=False)
print(f"  {len(orders_master):,} rows exported")

# ── Export 2: Category performance ──
print("Exporting category performance...")
category = conn.execute("""
    SELECT
        dp.category_english              AS category,
        COUNT(DISTINCT fo.order_id)      AS total_orders,
        ROUND(SUM(foi.price), 2)         AS total_revenue,
        ROUND(AVG(foi.price), 2)         AS avg_price,
        ROUND(AVG(foi.freight), 2)       AS avg_freight
    FROM fact_order_items foi
    JOIN fact_orders fo  ON foi.order_id  = fo.order_id
    JOIN dim_products dp ON foi.product_id = dp.product_id
    WHERE fo.is_delivered = true
    GROUP BY dp.category_english
    ORDER BY total_revenue DESC
""").fetchdf()

category.to_csv(f"{OUT_PATH}/category_performance.csv", index=False)
print(f"  {len(category):,} rows exported")

# ── Export 3: Customer summary ──
print("Exporting customer summary...")
customers = conn.execute("""
    SELECT
        dc.unique_customer_id,
        dc.city,
        dc.state,
        COUNT(DISTINCT fo.order_id)  AS total_orders,
        ROUND(SUM(foi.price), 2)     AS total_spent,
        MIN(fo.purchase_date)        AS first_order_date,
        MAX(fo.purchase_date)        AS last_order_date,
        CASE
            WHEN COUNT(DISTINCT fo.order_id) = 1 THEN 'One-time'
            WHEN COUNT(DISTINCT fo.order_id) = 2 THEN 'Returning'
            ELSE 'Loyal'
        END AS customer_type
    FROM fact_orders fo
    JOIN dim_customers dc     ON fo.customer_id = dc.customer_id
    JOIN fact_order_items foi ON fo.order_id    = foi.order_id
    WHERE fo.is_delivered = true
    GROUP BY dc.unique_customer_id, dc.city, dc.state
""").fetchdf()

customers.to_csv(f"{OUT_PATH}/customer_summary.csv", index=False)
print(f"  {len(customers):,} rows exported")

conn.close()
print("\nAll Power BI exports complete.")
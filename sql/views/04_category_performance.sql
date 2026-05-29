-- Category Performance
-- Business question: Which product categories drive the most revenue?
-- This tells us where to focus marketing and inventory investment.

SELECT
    dp.category_english                         AS category,
    COUNT(DISTINCT fo.order_id)                 AS total_orders,
    COUNT(DISTINCT fo.customer_id)              AS unique_customers,
    ROUND(SUM(foi.price), 2)                    AS total_revenue,
    ROUND(AVG(foi.price), 2)                    AS avg_item_price,
    ROUND(AVG(foi.freight), 2)                  AS avg_freight,
    ROUND(SUM(foi.price) * 100.0 /
        SUM(SUM(foi.price)) OVER (), 2)         AS revenue_share_pct
FROM fact_order_items foi
JOIN fact_orders fo   ON foi.order_id = fo.order_id
JOIN dim_products dp  ON foi.product_id = dp.product_id
WHERE fo.is_delivered = true
GROUP BY dp.category_english
ORDER BY total_revenue DESC
LIMIT 20
-- Monthly Revenue Trend
-- Business question: How has revenue grown month over month?
-- This tells us whether the business is growing, shrinking, or seasonal.

SELECT
    d.year,
    d.month,
    d.month_name,
    COUNT(DISTINCT fo.order_id)         AS total_orders,
    COUNT(DISTINCT fo.customer_id)      AS unique_customers,
    ROUND(SUM(foi.price), 2)            AS total_revenue,
    ROUND(AVG(foi.price), 2)            AS avg_order_value,
    ROUND(SUM(foi.freight), 2)          AS total_freight
FROM fact_orders fo
JOIN fact_order_items foi ON fo.order_id = foi.order_id
JOIN dim_date d           ON fo.purchase_date = d.date
WHERE fo.is_delivered = true
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year, d.month
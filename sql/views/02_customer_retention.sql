-- Customer Retention Analysis
-- Business question: What percentage of customers make a second purchase?
-- This is the single most important metric for any e-commerce business.

WITH customer_order_counts AS (
    -- Count how many orders each unique customer placed
    SELECT
        dc.unique_customer_id,
        COUNT(fo.order_id) AS total_orders
    FROM fact_orders fo
    JOIN dim_customers dc ON fo.customer_id = dc.customer_id
    WHERE fo.is_delivered = true
    GROUP BY dc.unique_customer_id
),
retention_buckets AS (
    -- Put each customer into a bucket based on order count
    SELECT
        unique_customer_id,
        total_orders,
        CASE
            WHEN total_orders = 1 THEN 'One-time buyer'
            WHEN total_orders = 2 THEN 'Returning buyer'
            WHEN total_orders >= 3 THEN 'Loyal buyer'
        END AS customer_type
    FROM customer_order_counts
)
SELECT
    customer_type,
    COUNT(*)                                    AS customer_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*))
          OVER (), 2)                           AS percentage
FROM retention_buckets
GROUP BY customer_type
ORDER BY customer_count DESC
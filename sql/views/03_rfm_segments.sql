-- RFM Segmentation
-- Business question: Who are our best customers?
-- RFM stands for Recency, Frequency, Monetary.
-- Recency  = how recently did they buy?
-- Frequency = how many times did they buy?
-- Monetary  = how much did they spend total?

WITH rfm_base AS (
    SELECT
        dc.unique_customer_id,
        -- Recency: days since last purchase (lower = better)
        DATEDIFF('day',
            MAX(fo.purchase_date),
            (SELECT MAX(purchase_date) FROM fact_orders)
        )                                       AS recency_days,
        -- Frequency: number of orders
        COUNT(DISTINCT fo.order_id)             AS frequency,
        -- Monetary: total amount spent
        ROUND(SUM(foi.price), 2)                AS monetary
    FROM fact_orders fo
    JOIN dim_customers dc     ON fo.customer_id = dc.customer_id
    JOIN fact_order_items foi ON fo.order_id = foi.order_id
    WHERE fo.is_delivered = true
    GROUP BY dc.unique_customer_id
),
rfm_scored AS (
    SELECT
        unique_customer_id,
        recency_days,
        frequency,
        monetary,
        -- Score each dimension 1-4 using quartiles
        NTILE(4) OVER (ORDER BY recency_days DESC)  AS r_score,
        NTILE(4) OVER (ORDER BY frequency ASC)      AS f_score,
        NTILE(4) OVER (ORDER BY monetary ASC)       AS m_score
    FROM rfm_base
)
SELECT
    unique_customer_id,
    recency_days,
    frequency,
    monetary,
    r_score,
    f_score,
    m_score,
    (r_score + f_score + m_score)               AS total_rfm_score,
    CASE
        WHEN (r_score + f_score + m_score) >= 10 THEN 'Champion'
        WHEN (r_score + f_score + m_score) >= 7  THEN 'Loyal'
        WHEN (r_score + f_score + m_score) >= 5  THEN 'At Risk'
        ELSE                                          'Lost'
    END                                         AS rfm_segment
FROM rfm_scored
ORDER BY total_rfm_score DESC
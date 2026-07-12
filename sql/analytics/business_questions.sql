-- =============================================================================
-- ANALYTICS QUERIES — Menjawab pertanyaan bisnis UMKM
-- Sumber: Data Warehouse (star schema) — fact_sales, fact_inventory, dim_*
-- =============================================================================
-- Query ditulis kompatibel SQLite & PostgreSQL (fungsi standar).
-- Untuk PostgreSQL, ganti tidak perlu; untuk perhitungan tanggal SQLite dipakai
-- fungsi date(). Jalankan per blok di DB client atau via dashboard.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- Q1. PRODUK PALING LARIS (by quantity & revenue)
-- -----------------------------------------------------------------------------
SELECT p.product_name, p.category, p.brand,
       SUM(f.quantity)      AS total_qty,
       SUM(f.net_revenue)   AS total_revenue,
       SUM(f.gross_profit)  AS total_profit
FROM fact_sales f
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p.product_name, p.category, p.brand
ORDER BY total_qty DESC
LIMIT 15;


-- -----------------------------------------------------------------------------
-- Q2. PRODUK DENGAN MARGIN TERTINGGI (kontribusi profit, margin >= threshold)
-- -----------------------------------------------------------------------------
SELECT p.product_name, p.category, p.margin_pct,
       SUM(f.quantity)     AS total_qty,
       SUM(f.net_revenue)  AS total_revenue,
       SUM(f.gross_profit) AS total_profit
FROM fact_sales f
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p.product_name, p.category, p.margin_pct
HAVING SUM(f.quantity) > 0
ORDER BY p.margin_pct DESC, total_profit DESC
LIMIT 15;


-- -----------------------------------------------------------------------------
-- Q2b. PRODUK REVENUE TINGGI TAPI MARGIN RENDAH (kandidat evaluasi supplier/bundling)
-- -----------------------------------------------------------------------------
SELECT p.product_name, p.category, p.margin_pct,
       SUM(f.net_revenue)  AS total_revenue,
       SUM(f.gross_profit) AS total_profit
FROM fact_sales f
JOIN dim_product p ON f.product_key = p.product_key
WHERE p.margin_pct < 25
GROUP BY p.product_name, p.category, p.margin_pct
ORDER BY total_revenue DESC
LIMIT 15;


-- -----------------------------------------------------------------------------
-- Q3. CABANG DENGAN REVENUE TERBAIK
-- -----------------------------------------------------------------------------
SELECT s.store_name, s.city, s.store_type,
       COUNT(DISTINCT f.transaction_id) AS n_transaksi,
       SUM(f.net_revenue)               AS total_revenue,
       SUM(f.gross_profit)              AS total_profit,
       ROUND(SUM(f.net_revenue) * 1.0 / COUNT(DISTINCT f.transaction_id), 0) AS avg_order_value
FROM fact_sales f
JOIN dim_store s ON f.store_key = s.store_key
GROUP BY s.store_name, s.city, s.store_type
ORDER BY total_revenue DESC;


-- -----------------------------------------------------------------------------
-- Q4. CUSTOMER REPEAT TERTINGGI (jumlah transaksi terbanyak)
-- -----------------------------------------------------------------------------
SELECT c.full_name, c.city, c.member_tier,
       COUNT(DISTINCT f.transaction_id) AS n_transaksi,
       SUM(f.net_revenue)               AS total_belanja
FROM fact_sales f
JOIN dim_customer c ON f.customer_key = c.customer_key
GROUP BY c.full_name, c.city, c.member_tier
HAVING COUNT(DISTINCT f.transaction_id) > 1
ORDER BY n_transaksi DESC, total_belanja DESC
LIMIT 20;


-- -----------------------------------------------------------------------------
-- Q4b. REPEAT CUSTOMER RATE (persentase pelanggan dengan >1 transaksi)
-- -----------------------------------------------------------------------------
WITH per_cust AS (
    SELECT customer_key, COUNT(DISTINCT transaction_id) AS n_trx
    FROM fact_sales
    WHERE customer_key IS NOT NULL
    GROUP BY customer_key
)
SELECT
    COUNT(*)                                              AS total_customer,
    SUM(CASE WHEN n_trx > 1 THEN 1 ELSE 0 END)            AS repeat_customer,
    ROUND(100.0 * SUM(CASE WHEN n_trx > 1 THEN 1 ELSE 0 END) / COUNT(*), 1)
                                                          AS repeat_rate_pct
FROM per_cust;


-- -----------------------------------------------------------------------------
-- Q5. PRODUK SLOW MOVING / DEAD STOCK
--     (masih ada stok tapi penjualan sangat kecil/nol)
-- -----------------------------------------------------------------------------
WITH sold AS (
    SELECT product_key, SUM(quantity) AS qty_sold
    FROM fact_sales
    GROUP BY product_key
),
stock AS (   -- stok terkini per produk (agregasi semua toko)
    SELECT product_key, SUM(stock_on_hand) AS stock_now
    FROM (
        SELECT product_key, store_key, stock_on_hand,
               ROW_NUMBER() OVER (PARTITION BY product_key, store_key
                                  ORDER BY date_key DESC) AS rn
        FROM fact_inventory
    ) t
    WHERE rn = 1
    GROUP BY product_key
)
SELECT p.product_name, p.category, p.brand,
       COALESCE(sold.qty_sold, 0) AS qty_sold_12m,
       COALESCE(stock.stock_now, 0) AS stok_saat_ini,
       p.cost_price * COALESCE(stock.stock_now, 0) AS nilai_stok_mengendap
FROM dim_product p
LEFT JOIN sold  ON p.product_key = sold.product_key
LEFT JOIN stock ON p.product_key = stock.product_key
WHERE COALESCE(sold.qty_sold, 0) <= 5
ORDER BY nilai_stok_mengendap DESC
LIMIT 20;


-- -----------------------------------------------------------------------------
-- Q6. REKOMENDASI RESTOCK
--     (stok menipis relatif terhadap kecepatan jual per bulan)
-- -----------------------------------------------------------------------------
WITH monthly_sales AS (
    SELECT product_key, SUM(quantity) / 12.0 AS avg_monthly_qty
    FROM fact_sales
    GROUP BY product_key
),
stock AS (
    SELECT product_key, SUM(stock_on_hand) AS stock_now
    FROM (
        SELECT product_key, store_key, stock_on_hand,
               ROW_NUMBER() OVER (PARTITION BY product_key, store_key
                                  ORDER BY date_key DESC) AS rn
        FROM fact_inventory
    ) t
    WHERE rn = 1
    GROUP BY product_key
)
SELECT p.product_name, p.category, p.brand,
       ROUND(m.avg_monthly_qty, 1) AS avg_jual_per_bulan,
       COALESCE(s.stock_now, 0)    AS stok_saat_ini,
       ROUND(COALESCE(s.stock_now, 0) / NULLIF(m.avg_monthly_qty, 0), 1)
                                   AS bulan_stok_tersisa,
       CASE
           WHEN COALESCE(s.stock_now,0) / NULLIF(m.avg_monthly_qty,0) < 1 THEN 'URGENT restock'
           WHEN COALESCE(s.stock_now,0) / NULLIF(m.avg_monthly_qty,0) < 2 THEN 'Segera restock'
           ELSE 'Aman'
       END AS rekomendasi
FROM dim_product p
JOIN monthly_sales m ON p.product_key = m.product_key
LEFT JOIN stock s ON p.product_key = s.product_key
WHERE m.avg_monthly_qty > 2
ORDER BY bulan_stok_tersisa ASC
LIMIT 20;


-- -----------------------------------------------------------------------------
-- Q7. TREN PENJUALAN BULANAN
-- -----------------------------------------------------------------------------
SELECT d.year, d.month, d.month_name,
       COUNT(DISTINCT f.transaction_id) AS n_transaksi,
       SUM(f.net_revenue)  AS revenue,
       SUM(f.gross_profit) AS profit
FROM fact_sales f
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year, d.month;


-- -----------------------------------------------------------------------------
-- Q8. CHANNEL PENJUALAN PALING EFEKTIF
-- -----------------------------------------------------------------------------
SELECT f.channel,
       COUNT(DISTINCT f.transaction_id) AS n_transaksi,
       SUM(f.net_revenue)  AS revenue,
       SUM(f.gross_profit) AS profit,
       ROUND(100.0 * SUM(f.gross_profit) / NULLIF(SUM(f.net_revenue),0), 1) AS margin_pct,
       ROUND(SUM(f.net_revenue) * 1.0 / COUNT(DISTINCT f.transaction_id), 0) AS avg_order_value
FROM fact_sales f
GROUP BY f.channel
ORDER BY revenue DESC;


-- -----------------------------------------------------------------------------
-- Q9. ANALISIS KATEGORI (kontribusi revenue & profit)
-- -----------------------------------------------------------------------------
SELECT p.parent_category, p.category,
       SUM(f.quantity)     AS total_qty,
       SUM(f.net_revenue)  AS revenue,
       SUM(f.gross_profit) AS profit,
       ROUND(100.0 * SUM(f.gross_profit) / NULLIF(SUM(f.net_revenue),0), 1) AS margin_pct
FROM fact_sales f
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p.parent_category, p.category
ORDER BY revenue DESC;


-- -----------------------------------------------------------------------------
-- Q10. STOCK TURNOVER per produk (COGS / rata-rata stok) — indikator perputaran
-- -----------------------------------------------------------------------------
WITH cogs AS (
    SELECT product_key, SUM(cost) AS total_cogs
    FROM fact_sales GROUP BY product_key
),
avg_stock AS (
    SELECT product_key, AVG(stock_on_hand) AS avg_stok
    FROM fact_inventory GROUP BY product_key
)
SELECT p.product_name, p.category,
       ROUND(c.total_cogs, 0) AS cogs,
       ROUND(a.avg_stok, 1)   AS rata_stok,
       ROUND(c.total_cogs / NULLIF(a.avg_stok, 0), 2) AS turnover_ratio
FROM dim_product p
JOIN cogs c     ON p.product_key = c.product_key
JOIN avg_stock a ON p.product_key = a.product_key
WHERE a.avg_stok > 0
ORDER BY turnover_ratio DESC
LIMIT 20;

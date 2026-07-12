-- =============================================================================
-- DATA WAREHOUSE — STAR SCHEMA (dimensional model)
-- Rumah Mode Nusantara — analitik penjualan & inventori
-- =============================================================================
-- Model dimensional (Kimball) untuk kebutuhan analitik/BI. Dipisahkan dari OLTP
-- agar query agregasi cepat dan mudah dipahami owner UMKM.
--
-- Rasional desain:
--  * Star schema (bukan snowflake) -> join minimal, performa & keterbacaan baik.
--  * Surrogate key (*_key) -> decouple dari natural key OLTP, siap SCD Type 2.
--  * fact_sales grain = 1 baris per line item penjualan -> agregasi fleksibel
--    ke level produk, kategori, cabang, channel, waktu, pelanggan.
--  * fact_inventory grain = 1 baris per pergerakan stok (harian) -> memungkinkan
--    perhitungan stock-on-hand, turnover, dan deteksi dead stock.
--
-- Kompatibel PostgreSQL (untuk SQLite dibuat otomatis oleh ETL via SQLAlchemy).
-- =============================================================================

DROP TABLE IF EXISTS fact_sales CASCADE;
DROP TABLE IF EXISTS fact_inventory CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;
DROP TABLE IF EXISTS dim_product CASCADE;
DROP TABLE IF EXISTS dim_customer CASCADE;
DROP TABLE IF EXISTS dim_store CASCADE;
DROP TABLE IF EXISTS dim_supplier CASCADE;

-- ----------------------------------------------------------------------------
-- DIMENSION: Tanggal
-- ----------------------------------------------------------------------------
CREATE TABLE dim_date (
    date_key           INTEGER PRIMARY KEY,   -- format YYYYMMDD
    full_date          DATE    NOT NULL,
    day                INTEGER NOT NULL,
    month              INTEGER NOT NULL,
    month_name         VARCHAR(15) NOT NULL,
    quarter            INTEGER NOT NULL,
    year               INTEGER NOT NULL,
    day_of_week        INTEGER NOT NULL,      -- 0=Senin .. 6=Minggu
    day_name           VARCHAR(15) NOT NULL,
    is_weekend         BOOLEAN NOT NULL,
    is_holiday_season  BOOLEAN NOT NULL       -- Ramadan/Lebaran, Harbolnas, akhir tahun
);

-- ----------------------------------------------------------------------------
-- DIMENSION: Produk
-- ----------------------------------------------------------------------------
CREATE TABLE dim_product (
    product_key     SERIAL PRIMARY KEY,
    product_id      INTEGER NOT NULL,          -- natural key dari OLTP
    sku             VARCHAR(30) NOT NULL,
    product_name    VARCHAR(120) NOT NULL,
    category        VARCHAR(50) NOT NULL,
    parent_category VARCHAR(50) NOT NULL,
    brand           VARCHAR(50) NOT NULL,
    size            VARCHAR(10) NOT NULL,
    color           VARCHAR(30) NOT NULL,
    cost_price      NUMERIC(12,2) NOT NULL,
    sell_price      NUMERIC(12,2) NOT NULL,
    margin_pct      NUMERIC(6,2) NOT NULL      -- (sell-cost)/sell * 100
);

-- ----------------------------------------------------------------------------
-- DIMENSION: Pelanggan
-- ----------------------------------------------------------------------------
CREATE TABLE dim_customer (
    customer_key    SERIAL PRIMARY KEY,
    customer_id     INTEGER NOT NULL,
    full_name       VARCHAR(100) NOT NULL,
    gender          VARCHAR(10),
    age_group       VARCHAR(15),               -- <20, 20-29, 30-39, 40-49, 50+
    city            VARCHAR(50),
    member_tier     VARCHAR(10) NOT NULL,
    join_date       DATE
);

-- ----------------------------------------------------------------------------
-- DIMENSION: Toko / cabang
-- ----------------------------------------------------------------------------
CREATE TABLE dim_store (
    store_key       SERIAL PRIMARY KEY,
    store_id        INTEGER NOT NULL,
    store_name      VARCHAR(80) NOT NULL,
    city            VARCHAR(50) NOT NULL,
    province        VARCHAR(50) NOT NULL,
    store_type      VARCHAR(20) NOT NULL
);

-- ----------------------------------------------------------------------------
-- DIMENSION: Supplier
-- ----------------------------------------------------------------------------
CREATE TABLE dim_supplier (
    supplier_key    SERIAL PRIMARY KEY,
    supplier_id     INTEGER NOT NULL,
    supplier_name   VARCHAR(100) NOT NULL,
    city            VARCHAR(50) NOT NULL,
    lead_time_days  INTEGER NOT NULL
);

-- ----------------------------------------------------------------------------
-- FACT: Penjualan (grain = line item)
-- ----------------------------------------------------------------------------
CREATE TABLE fact_sales (
    sales_key       SERIAL PRIMARY KEY,
    date_key        INTEGER NOT NULL REFERENCES dim_date(date_key),
    product_key     INTEGER NOT NULL REFERENCES dim_product(product_key),
    customer_key    INTEGER REFERENCES dim_customer(customer_key),
    store_key       INTEGER NOT NULL REFERENCES dim_store(store_key),
    transaction_id  INTEGER NOT NULL,          -- degenerate dimension
    channel         VARCHAR(20) NOT NULL,
    quantity        INTEGER NOT NULL,
    gross_revenue   NUMERIC(14,2) NOT NULL,    -- quantity * unit_price
    discount        NUMERIC(14,2) NOT NULL DEFAULT 0,
    net_revenue     NUMERIC(14,2) NOT NULL,    -- gross - discount (alokasi)
    cost            NUMERIC(14,2) NOT NULL,    -- quantity * unit_cost
    gross_profit    NUMERIC(14,2) NOT NULL     -- net_revenue - cost
);

-- ----------------------------------------------------------------------------
-- FACT: Inventori (grain = pergerakan stok harian per produk per toko)
-- ----------------------------------------------------------------------------
CREATE TABLE fact_inventory (
    inventory_key   SERIAL PRIMARY KEY,
    date_key        INTEGER NOT NULL REFERENCES dim_date(date_key),
    product_key     INTEGER NOT NULL REFERENCES dim_product(product_key),
    store_key       INTEGER NOT NULL REFERENCES dim_store(store_key),
    qty_in          INTEGER NOT NULL DEFAULT 0,
    qty_out         INTEGER NOT NULL DEFAULT 0,
    stock_on_hand   INTEGER NOT NULL DEFAULT 0   -- saldo stok kumulatif
);

-- ----------------------------------------------------------------------------
-- Index pada foreign key fact untuk performa query analitik
-- ----------------------------------------------------------------------------
CREATE INDEX idx_fs_date    ON fact_sales(date_key);
CREATE INDEX idx_fs_product ON fact_sales(product_key);
CREATE INDEX idx_fs_store   ON fact_sales(store_key);
CREATE INDEX idx_fs_cust    ON fact_sales(customer_key);
CREATE INDEX idx_fi_date    ON fact_inventory(date_key);
CREATE INDEX idx_fi_product ON fact_inventory(product_key);
CREATE INDEX idx_fi_store   ON fact_inventory(store_key);

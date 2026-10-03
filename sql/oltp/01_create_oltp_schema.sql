-- =============================================================================
-- OLTP SCHEMA - Rumah Mode Nusantara (UMKM Fashion Retail)
-- =============================================================================
-- Skema transaksional (Operational / OLTP) yang menormalkan proses bisnis:
-- master data (kategori, produk, supplier, toko, pelanggan), penjualan,
-- pembelian (purchase order), dan pergerakan inventori.
--
-- Kompatibel PostgreSQL. Untuk fallback SQLite, tabel dibuat oleh ETL via
-- SQLAlchemy (tipe SERIAL/DATE dipetakan otomatis). Jalankan file ini manual
-- hanya bila memakai PostgreSQL:
--     psql -d umkm_bi -f sql/oltp/01_create_oltp_schema.sql
-- =============================================================================

DROP TABLE IF EXISTS inventory_movements CASCADE;
DROP TABLE IF EXISTS po_details CASCADE;
DROP TABLE IF EXISTS purchase_orders CASCADE;
DROP TABLE IF EXISTS sales_details CASCADE;
DROP TABLE IF EXISTS sales_transactions CASCADE;
DROP TABLE IF EXISTS marketing_campaigns CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS suppliers CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS stores CASCADE;

-- ----------------------------------------------------------------------------
-- Master: Kategori produk
-- ----------------------------------------------------------------------------
CREATE TABLE categories (
    category_id     SERIAL PRIMARY KEY,
    category_name   VARCHAR(50)  NOT NULL,
    parent_category VARCHAR(50)  NOT NULL
);

-- ----------------------------------------------------------------------------
-- Master: Supplier / pemasok
-- ----------------------------------------------------------------------------
CREATE TABLE suppliers (
    supplier_id     SERIAL PRIMARY KEY,
    supplier_name   VARCHAR(100) NOT NULL,
    city            VARCHAR(50)  NOT NULL,
    contact         VARCHAR(30),
    lead_time_days  INTEGER      NOT NULL DEFAULT 7
);

-- ----------------------------------------------------------------------------
-- Master: Produk (SKU) fashion - punya size, color, brand
-- ----------------------------------------------------------------------------
CREATE TABLE products (
    product_id      SERIAL PRIMARY KEY,
    sku             VARCHAR(30)  NOT NULL UNIQUE,
    product_name    VARCHAR(120) NOT NULL,
    category_id     INTEGER      NOT NULL REFERENCES categories(category_id),
    brand           VARCHAR(50)  NOT NULL,
    size            VARCHAR(10)  NOT NULL,
    color           VARCHAR(30)  NOT NULL,
    cost_price      NUMERIC(12,2) NOT NULL,   -- harga modal (Rupiah)
    sell_price      NUMERIC(12,2) NOT NULL,   -- harga jual (Rupiah)
    supplier_id     INTEGER      REFERENCES suppliers(supplier_id),
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE
);

-- ----------------------------------------------------------------------------
-- Master: Toko / cabang
-- ----------------------------------------------------------------------------
CREATE TABLE stores (
    store_id        SERIAL PRIMARY KEY,
    store_name      VARCHAR(80)  NOT NULL,
    city            VARCHAR(50)  NOT NULL,
    province        VARCHAR(50)  NOT NULL,
    store_type      VARCHAR(20)  NOT NULL,     -- flagship / regular
    open_date       DATE         NOT NULL
);

-- ----------------------------------------------------------------------------
-- Master: Pelanggan
-- ----------------------------------------------------------------------------
CREATE TABLE customers (
    customer_id     SERIAL PRIMARY KEY,
    full_name       VARCHAR(100) NOT NULL,
    gender          VARCHAR(10),
    birth_year      INTEGER,
    city            VARCHAR(50),
    join_date       DATE         NOT NULL,
    member_tier     VARCHAR(10)  NOT NULL DEFAULT 'Bronze'
);

-- ----------------------------------------------------------------------------
-- Transaksi penjualan (header)
-- ----------------------------------------------------------------------------
CREATE TABLE sales_transactions (
    transaction_id    SERIAL PRIMARY KEY,
    store_id          INTEGER NOT NULL REFERENCES stores(store_id),
    customer_id       INTEGER REFERENCES customers(customer_id),
    channel           VARCHAR(20) NOT NULL,   -- offline/shopee/tokopedia/instagram
    transaction_date  DATE    NOT NULL,
    payment_method    VARCHAR(20),
    total_amount      NUMERIC(14,2) NOT NULL, -- net setelah diskon
    discount_amount   NUMERIC(14,2) NOT NULL DEFAULT 0
);

-- ----------------------------------------------------------------------------
-- Detail penjualan (line item) - grain 1 baris per produk per transaksi
-- ----------------------------------------------------------------------------
CREATE TABLE sales_details (
    detail_id       SERIAL PRIMARY KEY,
    transaction_id  INTEGER NOT NULL REFERENCES sales_transactions(transaction_id),
    product_id      INTEGER NOT NULL REFERENCES products(product_id),
    quantity        INTEGER NOT NULL,
    unit_price      NUMERIC(12,2) NOT NULL,   -- harga jual saat transaksi
    unit_cost       NUMERIC(12,2) NOT NULL,   -- harga modal saat transaksi
    line_total      NUMERIC(14,2) NOT NULL    -- quantity * unit_price
);

-- ----------------------------------------------------------------------------
-- Purchase Order (header) - pembelian stok ke supplier
-- ----------------------------------------------------------------------------
CREATE TABLE purchase_orders (
    po_id           SERIAL PRIMARY KEY,
    supplier_id     INTEGER NOT NULL REFERENCES suppliers(supplier_id),
    store_id        INTEGER NOT NULL REFERENCES stores(store_id),
    order_date      DATE    NOT NULL,
    received_date   DATE,
    status          VARCHAR(20) NOT NULL DEFAULT 'received',  -- ordered/received/cancelled
    total_cost      NUMERIC(14,2) NOT NULL DEFAULT 0
);

-- ----------------------------------------------------------------------------
-- Purchase Order (detail)
-- ----------------------------------------------------------------------------
CREATE TABLE po_details (
    po_detail_id    SERIAL PRIMARY KEY,
    po_id           INTEGER NOT NULL REFERENCES purchase_orders(po_id),
    product_id      INTEGER NOT NULL REFERENCES products(product_id),
    quantity        INTEGER NOT NULL,
    unit_cost       NUMERIC(12,2) NOT NULL
);

-- ----------------------------------------------------------------------------
-- Pergerakan inventori (stock ledger)
-- ----------------------------------------------------------------------------
CREATE TABLE inventory_movements (
    movement_id     SERIAL PRIMARY KEY,
    store_id        INTEGER NOT NULL REFERENCES stores(store_id),
    product_id      INTEGER NOT NULL REFERENCES products(product_id),
    movement_date   DATE    NOT NULL,
    movement_type   VARCHAR(15) NOT NULL,     -- in / out / adjustment
    quantity        INTEGER NOT NULL,         -- positif=masuk, negatif=keluar
    reference       VARCHAR(40)               -- mis. PO#123 / TRX#456
);

-- ----------------------------------------------------------------------------
-- Kampanye marketing (opsional)
-- ----------------------------------------------------------------------------
CREATE TABLE marketing_campaigns (
    campaign_id     SERIAL PRIMARY KEY,
    campaign_name   VARCHAR(80) NOT NULL,
    channel         VARCHAR(20) NOT NULL,
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    budget          NUMERIC(14,2) NOT NULL DEFAULT 0,
    discount_pct    NUMERIC(5,2)  NOT NULL DEFAULT 0
);

-- ----------------------------------------------------------------------------
-- Index untuk mempercepat join & filter analitik
-- ----------------------------------------------------------------------------
CREATE INDEX idx_sales_trx_date   ON sales_transactions(transaction_date);
CREATE INDEX idx_sales_trx_store  ON sales_transactions(store_id);
CREATE INDEX idx_sales_trx_cust   ON sales_transactions(customer_id);
CREATE INDEX idx_sales_det_trx    ON sales_details(transaction_id);
CREATE INDEX idx_sales_det_prod   ON sales_details(product_id);
CREATE INDEX idx_invmov_prod      ON inventory_movements(product_id);
CREATE INDEX idx_invmov_store     ON inventory_movements(store_id);

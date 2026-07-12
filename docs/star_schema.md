# Star Schema — Data Warehouse

Model dimensional (Kimball) untuk analitik. Dua fact table berbagi dimensi (*conformed
dimensions*): `dim_date`, `dim_product`, `dim_store`.

```mermaid
erDiagram
    dim_date     ||--o{ fact_sales : ""
    dim_product  ||--o{ fact_sales : ""
    dim_customer ||--o{ fact_sales : ""
    dim_store    ||--o{ fact_sales : ""
    dim_date     ||--o{ fact_inventory : ""
    dim_product  ||--o{ fact_inventory : ""
    dim_store    ||--o{ fact_inventory : ""

    fact_sales {
        int sales_key PK
        int date_key FK
        int product_key FK
        int customer_key FK
        int store_key FK
        int transaction_id "degenerate dim"
        varchar channel
        int quantity
        numeric gross_revenue
        numeric discount
        numeric net_revenue
        numeric cost
        numeric gross_profit
    }
    fact_inventory {
        int inventory_key PK
        int date_key FK
        int product_key FK
        int store_key FK
        int qty_in
        int qty_out
        int stock_on_hand
    }
    dim_date {
        int date_key PK
        date full_date
        varchar month_name
        int quarter
        int year
        boolean is_weekend
        boolean is_holiday_season
    }
    dim_product {
        int product_key PK
        int product_id
        varchar sku
        varchar category
        varchar parent_category
        varchar brand
        varchar size
        varchar color
        numeric margin_pct
    }
    dim_customer {
        int customer_key PK
        int customer_id
        varchar gender
        varchar age_group
        varchar city
        varchar member_tier
    }
    dim_store {
        int store_key PK
        int store_id
        varchar store_name
        varchar city
        varchar store_type
    }
    dim_supplier {
        int supplier_key PK
        int supplier_id
        varchar supplier_name
        int lead_time_days
    }
```

## Alasan Desain

- **Star (bukan snowflake):** dimensi didenormalisasi → join minimal, query agregasi cepat,
  dan mudah dipahami analis/owner non-teknis.
- **Grain `fact_sales` = line item:** memungkinkan agregasi fleksibel ke level produk,
  kategori, brand, ukuran/warna, cabang, channel, pelanggan, dan waktu tanpa kehilangan detail.
- **Grain `fact_inventory` = pergerakan harian:** mendukung perhitungan `stock_on_hand`
  kumulatif, *stock turnover*, dan deteksi *dead stock*.
- **Surrogate key (`*_key`):** memisahkan warehouse dari natural key OLTP, mempermudah
  penerapan **SCD (Slowly Changing Dimension)** di masa depan.
- **Conformed dimensions:** `dim_date`, `dim_product`, `dim_store` dipakai kedua fact →
  analisis lintas proses (penjualan vs stok) konsisten.
- **Degenerate dimension** `transaction_id` disimpan di fact untuk analisis level keranjang
  (jumlah item per transaksi, AOV).

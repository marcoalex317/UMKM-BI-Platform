# Power BI — Panduan Koneksi & Measures

Dashboard utama proyek ini dibangun dengan **Streamlit** (code-based, dapat direview di
GitHub). Berikut panduan mereplikasi analitik yang sama di **Power BI** sebagai alternatif
(mis. untuk stakeholder yang terbiasa dengan Microsoft BI).

## 1. Menyiapkan Sumber Data

Power BI Desktop dapat terhubung ke warehouse melalui salah satu cara:

**Opsi A — PostgreSQL (disarankan untuk Power BI)**
1. Set `.env` → `DB_ENGINE=postgres`, lalu jalankan `python etl/run_pipeline.py`.
2. Di Power BI: **Get Data → PostgreSQL database** → isi host, database `umkm_bi`.
3. Pilih tabel: `fact_sales`, `fact_inventory`, `dim_date`, `dim_product`,
   `dim_customer`, `dim_store`, `dim_supplier`.

**Opsi B — dari CSV**
1. **Get Data → Text/CSV** dari folder `data/raw/` (atau export tabel DWH ke CSV).

## 2. Model Relasi (Star Schema)

Buat relasi *many-to-one* dari fact ke dimension:

| Dari (fact) | Ke (dimension) | Kolom |
|-------------|----------------|-------|
| fact_sales | dim_date | date_key |
| fact_sales | dim_product | product_key |
| fact_sales | dim_customer | customer_key |
| fact_sales | dim_store | store_key |
| fact_inventory | dim_date | date_key |
| fact_inventory | dim_product | product_key |
| fact_inventory | dim_store | store_key |

Tandai `dim_date` sebagai **Date table** (Mark as date table → full_date).

## 3. Contoh DAX Measures

```dax
Total Revenue      = SUM ( fact_sales[net_revenue] )
Gross Profit       = SUM ( fact_sales[gross_profit] )
Gross Margin %     = DIVIDE ( [Gross Profit], [Total Revenue] )
Total Qty          = SUM ( fact_sales[quantity] )
Jumlah Transaksi   = DISTINCTCOUNT ( fact_sales[transaction_id] )
Avg Order Value    = DIVIDE ( [Total Revenue], [Jumlah Transaksi] )

Repeat Customers =
VAR TrxPerCust =
    ADDCOLUMNS (
        VALUES ( dim_customer[customer_key] ),
        "@n", CALCULATE ( DISTINCTCOUNT ( fact_sales[transaction_id] ) )
    )
RETURN
    COUNTROWS ( FILTER ( TrxPerCust, [@n] > 1 ) )

Repeat Rate % =
DIVIDE ( [Repeat Customers], DISTINCTCOUNT ( fact_sales[customer_key] ) )

Stock On Hand =
CALCULATE (
    SUM ( fact_inventory[stock_on_hand] ),
    FILTER (
        fact_inventory,
        fact_inventory[date_key] = MAX ( fact_inventory[date_key] )
    )
)
```

## 4. Halaman yang Disarankan
Replikasikan 6 halaman Streamlit: **Executive Overview, Sales Performance,
Product & Category, Inventory & Restock, Customer Analysis, Branch Performance** —
dengan KPI card (measures di atas), slicer (Tanggal, Cabang, Channel), dan visual
bar/line/donut/table yang setara.

> Simpan file `.pbix` di folder ini. Karena `.pbix` biner (tidak bisa di-diff di GitHub),
> lampirkan juga screenshot hasilnya ke `assets/screenshots/`.

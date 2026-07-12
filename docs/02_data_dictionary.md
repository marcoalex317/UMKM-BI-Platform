# Data Dictionary

Dokumentasi seluruh tabel pada dua layer: **OLTP** (transaksional) dan **DWH** (star schema).

---

## A. OLTP Layer (schema transaksional)

### `categories`
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| category_id | INT (PK) | ID kategori |
| category_name | VARCHAR | Sub-kategori (mis. Kemeja, Rok) |
| parent_category | VARCHAR | Kategori induk (Atasan, Bawahan, Dress, Outerwear, Aksesoris) |

### `suppliers`
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| supplier_id | INT (PK) | ID supplier |
| supplier_name | VARCHAR | Nama pemasok |
| city | VARCHAR | Kota supplier |
| contact | VARCHAR | Nomor kontak |
| lead_time_days | INT | Waktu tunggu pengiriman (hari) |

### `products`
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| product_id | INT (PK) | ID produk / SKU |
| sku | VARCHAR (unique) | Kode SKU |
| product_name | VARCHAR | Nama produk |
| category_id | INT (FK) | → categories |
| brand | VARCHAR | Brand lokal |
| size | VARCHAR | Ukuran (S/M/L/XL/All Size) |
| color | VARCHAR | Warna |
| cost_price | NUMERIC | Harga modal (Rp) |
| sell_price | NUMERIC | Harga jual (Rp) |
| supplier_id | INT (FK) | → suppliers |
| is_active | BOOLEAN | Status aktif |

### `stores`
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| store_id | INT (PK) | ID cabang |
| store_name | VARCHAR | Nama cabang |
| city / province | VARCHAR | Lokasi |
| store_type | VARCHAR | flagship / regular |
| open_date | DATE | Tanggal buka |

### `customers`
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| customer_id | INT (PK) | ID pelanggan |
| full_name | VARCHAR | Nama |
| gender | VARCHAR | Pria/Wanita (bisa "Tidak Diketahui" setelah cleaning) |
| birth_year | INT | Tahun lahir |
| city | VARCHAR | Kota |
| join_date | DATE | Tanggal bergabung |
| member_tier | VARCHAR | Bronze / Silver / Gold |

### `sales_transactions` (header)
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| transaction_id | INT (PK) | ID transaksi |
| store_id | INT (FK) | → stores |
| customer_id | INT (FK, nullable) | → customers (NULL = guest) |
| channel | VARCHAR | offline / shopee / tokopedia / instagram |
| transaction_date | DATE | Tanggal transaksi |
| payment_method | VARCHAR | Metode bayar |
| total_amount | NUMERIC | Net setelah diskon |
| discount_amount | NUMERIC | Total diskon transaksi |

### `sales_details` (line item)
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| detail_id | INT (PK) | ID baris |
| transaction_id | INT (FK) | → sales_transactions |
| product_id | INT (FK) | → products |
| quantity | INT | Jumlah unit |
| unit_price | NUMERIC | Harga jual saat transaksi |
| unit_cost | NUMERIC | Harga modal saat transaksi |
| line_total | NUMERIC | quantity × unit_price |

### `purchase_orders` / `po_details`
Pembelian stok ke supplier (header & detail): supplier_id, store_id, order_date,
received_date, status, total_cost; detail: product_id, quantity, unit_cost.

### `inventory_movements`
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| movement_id | INT (PK) | ID pergerakan |
| store_id, product_id | INT (FK) | Lokasi & produk |
| movement_date | DATE | Tanggal |
| movement_type | VARCHAR | in / out / adjustment |
| quantity | INT | +masuk / −keluar |
| reference | VARCHAR | mis. PO#123 / TRX#456 |

### `marketing_campaigns`
campaign_id, campaign_name, channel, start_date, end_date, budget, discount_pct.

---

## B. Data Warehouse Layer (star schema)

### Dimensions
| Tabel | Surrogate Key | Atribut penting |
|-------|---------------|-----------------|
| `dim_date` | date_key (YYYYMMDD) | full_date, month_name, quarter, year, is_weekend, is_holiday_season |
| `dim_product` | product_key | product_id, sku, category, parent_category, brand, size, color, cost/sell price, **margin_pct** |
| `dim_customer` | customer_key | customer_id, gender, **age_group**, city, member_tier |
| `dim_store` | store_key | store_id, store_name, city, province, store_type |
| `dim_supplier` | supplier_key | supplier_id, supplier_name, city, lead_time_days |

### Facts
| Tabel | Grain | Measure |
|-------|-------|---------|
| `fact_sales` | 1 baris / line item penjualan | quantity, gross_revenue, discount, **net_revenue**, cost, **gross_profit** |
| `fact_inventory` | 1 baris / pergerakan stok harian per produk per toko | qty_in, qty_out, **stock_on_hand** (saldo kumulatif) |

**Catatan turunan:**
- `margin_pct` = (sell_price − cost_price) / sell_price × 100
- `net_revenue` = gross_revenue − discount (diskon dialokasikan proporsional per line item)
- `gross_profit` = net_revenue − cost
- `stock_on_hand` = kumulatif (qty_in − qty_out) diurutkan per tanggal per (produk, toko)

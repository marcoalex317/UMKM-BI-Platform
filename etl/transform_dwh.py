"""
transform_dwh.py
================
Transformasi OLTP -> Data Warehouse (star schema).

Membangun:
  dim_date, dim_product, dim_customer, dim_store, dim_supplier
  fact_sales (grain: line item), fact_inventory (grain: gerakan stok harian)

Semua dilakukan dengan pandas lalu ditulis ke DB via SQLAlchemy sehingga
kompatibel SQLite & PostgreSQL. Surrogate key dibuat berurutan (1..N).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import config as cfg

MONTH_ID = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
    7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember",
}
DAY_ID = {0: "Senin", 1: "Selasa", 2: "Rabu", 3: "Kamis",
          4: "Jumat", 5: "Sabtu", 6: "Minggu"}


def _read(conn, table: str) -> pd.DataFrame:
    return pd.read_sql(f"SELECT * FROM {table}", conn)


def _age_group(birth_year) -> str:
    if pd.isna(birth_year):
        return "Tidak Diketahui"
    age = 2026 - int(birth_year)
    if age < 20:
        return "<20"
    if age < 30:
        return "20-29"
    if age < 40:
        return "30-39"
    if age < 50:
        return "40-49"
    return "50+"


# --------------------------------------------------------------------------- #
# Dimensions
# --------------------------------------------------------------------------- #
def build_dim_date() -> pd.DataFrame:
    start = pd.to_datetime(cfg.DATA_START)
    # perluas rentang agar mencakup tanggal PO awal (sebelum periode)
    start = start - pd.Timedelta(days=30)
    end = pd.to_datetime(cfg.DATA_END) + pd.Timedelta(days=15)
    dates = pd.date_range(start, end, freq="D")
    df = pd.DataFrame({"full_date": dates})
    df["date_key"] = df["full_date"].dt.strftime("%Y%m%d").astype(int)
    df["day"] = df["full_date"].dt.day
    df["month"] = df["full_date"].dt.month
    df["month_name"] = df["month"].map(MONTH_ID)
    df["quarter"] = df["full_date"].dt.quarter
    df["year"] = df["full_date"].dt.year
    df["day_of_week"] = df["full_date"].dt.weekday
    df["day_name"] = df["day_of_week"].map(DAY_ID)
    df["is_weekend"] = df["day_of_week"] >= 5
    df["is_holiday_season"] = df["month"].isin([3, 4, 11, 12])
    df["full_date"] = df["full_date"].dt.strftime("%Y-%m-%d")
    return df[["date_key", "full_date", "day", "month", "month_name", "quarter",
               "year", "day_of_week", "day_name", "is_weekend", "is_holiday_season"]]


def build_dim_product(products, categories) -> pd.DataFrame:
    df = products.merge(categories, on="category_id", how="left")
    df["margin_pct"] = np.where(
        df["sell_price"] > 0,
        (df["sell_price"] - df["cost_price"]) / df["sell_price"] * 100, 0).round(2)
    df = df.reset_index(drop=True)
    df.insert(0, "product_key", np.arange(1, len(df) + 1))
    return df.rename(columns={"category_name": "category"})[[
        "product_key", "product_id", "sku", "product_name", "category",
        "parent_category", "brand", "size", "color",
        "cost_price", "sell_price", "margin_pct"]]


def build_dim_customer(customers) -> pd.DataFrame:
    df = customers.copy()
    df["age_group"] = df["birth_year"].apply(_age_group)
    df = df.reset_index(drop=True)
    df.insert(0, "customer_key", np.arange(1, len(df) + 1))
    return df[["customer_key", "customer_id", "full_name", "gender",
               "age_group", "city", "member_tier", "join_date"]]


def build_dim_store(stores) -> pd.DataFrame:
    df = stores.reset_index(drop=True).copy()
    df.insert(0, "store_key", np.arange(1, len(df) + 1))
    return df[["store_key", "store_id", "store_name", "city", "province", "store_type"]]


def build_dim_supplier(suppliers) -> pd.DataFrame:
    df = suppliers.reset_index(drop=True).copy()
    df.insert(0, "supplier_key", np.arange(1, len(df) + 1))
    return df[["supplier_key", "supplier_id", "supplier_name", "city", "lead_time_days"]]


# --------------------------------------------------------------------------- #
# Facts
# --------------------------------------------------------------------------- #
def build_fact_sales(sales_det, sales_trx, dim_product, dim_customer,
                     dim_store, dim_date) -> pd.DataFrame:
    # dedup detail (jaga-jaga bila ada sisa duplikat)
    det = sales_det.drop_duplicates(subset=["detail_id"]).copy()
    df = det.merge(sales_trx, on="transaction_id", how="left")

    # hitung ukuran (gross) & alokasi diskon proporsional per transaksi
    df["gross_revenue"] = df["quantity"] * df["unit_price"]
    trx_gross = df.groupby("transaction_id")["gross_revenue"].transform("sum")
    df["discount"] = np.where(
        trx_gross > 0,
        df["discount_amount"] * df["gross_revenue"] / trx_gross, 0).round(2)
    df["net_revenue"] = (df["gross_revenue"] - df["discount"]).round(2)
    df["cost"] = (df["quantity"] * df["unit_cost"]).round(2)
    df["gross_profit"] = (df["net_revenue"] - df["cost"]).round(2)

    # surrogate keys via mapping
    pk = dim_product.set_index("product_id")["product_key"]
    sk = dim_store.set_index("store_id")["store_key"]
    ck = dim_customer.set_index("customer_id")["customer_key"]
    df["product_key"] = df["product_id"].map(pk)
    df["store_key"] = df["store_id"].map(sk)
    df["customer_key"] = df["customer_id"].map(ck)   # NaN untuk guest
    df["date_key"] = pd.to_datetime(df["transaction_date"]).dt.strftime("%Y%m%d").astype(int)

    df = df.reset_index(drop=True)
    df.insert(0, "sales_key", np.arange(1, len(df) + 1))
    # customer_key jadi nullable integer
    df["customer_key"] = df["customer_key"].astype("Int64")
    return df[["sales_key", "date_key", "product_key", "customer_key", "store_key",
               "transaction_id", "channel", "quantity", "gross_revenue",
               "discount", "net_revenue", "cost", "gross_profit"]]


def build_fact_inventory(inv, dim_product, dim_store) -> pd.DataFrame:
    df = inv.copy()
    df["movement_date"] = pd.to_datetime(df["movement_date"])
    df["date_key"] = df["movement_date"].dt.strftime("%Y%m%d").astype(int)
    df["qty_in"] = np.where(df["quantity"] > 0, df["quantity"], 0)
    df["qty_out"] = np.where(df["quantity"] < 0, -df["quantity"], 0)

    pk = dim_product.set_index("product_id")["product_key"]
    sk = dim_store.set_index("store_id")["store_key"]
    df["product_key"] = df["product_id"].map(pk)
    df["store_key"] = df["store_id"].map(sk)

    # agregasi harian per produk per toko
    grp = (df.groupby(["date_key", "product_key", "store_key"], as_index=False)
             .agg(qty_in=("qty_in", "sum"), qty_out=("qty_out", "sum")))

    # stock_on_hand kumulatif per (produk, toko) berdasarkan urutan tanggal
    grp = grp.sort_values(["product_key", "store_key", "date_key"])
    grp["net"] = grp["qty_in"] - grp["qty_out"]
    grp["stock_on_hand"] = grp.groupby(["product_key", "store_key"])["net"].cumsum()
    grp = grp.drop(columns="net").reset_index(drop=True)
    grp.insert(0, "inventory_key", np.arange(1, len(grp) + 1))
    return grp[["inventory_key", "date_key", "product_key", "store_key",
                "qty_in", "qty_out", "stock_on_hand"]]


# --------------------------------------------------------------------------- #
# Orkestrasi
# --------------------------------------------------------------------------- #
def transform() -> None:
    engine = cfg.get_engine()
    print(f"[transform_dwh] Sumber & target: {cfg.engine_label()}")

    with engine.connect() as conn:
        products = _read(conn, "products")
        categories = _read(conn, "categories")
        customers = _read(conn, "customers")
        stores = _read(conn, "stores")
        suppliers = _read(conn, "suppliers")
        sales_trx = _read(conn, "sales_transactions")
        sales_det = _read(conn, "sales_details")
        inv = _read(conn, "inventory_movements")

    dim_date = build_dim_date()
    dim_product = build_dim_product(products, categories)
    dim_customer = build_dim_customer(customers)
    dim_store = build_dim_store(stores)
    dim_supplier = build_dim_supplier(suppliers)
    fact_sales = build_fact_sales(sales_det, sales_trx, dim_product,
                                  dim_customer, dim_store, dim_date)
    fact_inventory = build_fact_inventory(inv, dim_product, dim_store)

    outputs = {
        "dim_date": dim_date,
        "dim_product": dim_product,
        "dim_customer": dim_customer,
        "dim_store": dim_store,
        "dim_supplier": dim_supplier,
        "fact_sales": fact_sales,
        "fact_inventory": fact_inventory,
    }
    with engine.begin() as conn:
        for name, df in outputs.items():
            df.to_sql(name, conn, if_exists="replace", index=False)
            print(f"  - {name:16s}: {len(df):>7,} baris")

    # Rekonsiliasi: net_revenue fact_sales vs (gross-discount) OLTP
    oltp_net = round(float(sales_trx["total_amount"].sum()), 2)
    dwh_net = round(float(fact_sales["net_revenue"].sum()), 2)
    diff = round(abs(oltp_net - dwh_net), 2)
    print(f"[transform_dwh] Rekonsiliasi net revenue: "
          f"OLTP={oltp_net:,.0f} vs DWH={dwh_net:,.0f} (selisih {diff:,.0f})")


if __name__ == "__main__":
    transform()

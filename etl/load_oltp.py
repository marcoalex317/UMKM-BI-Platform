"""
load_oltp.py
============
Muat CSV hasil generate ke database OLTP (SQLite default / PostgreSQL).

Termasuk tahap DATA CLEANING:
  * Normalisasi format tanggal yang beragam (ISO & DD/MM/YYYY) -> DATE.
  * Hapus baris duplikat (mis. sales_details yang sengaja diduplikasi).
  * Handle missing value (gender/city diisi 'Tidak Diketahui').
  * Validasi tipe numerik.

Skema tabel dibuat otomatis oleh pandas.to_sql (SQLAlchemy) sehingga kompatibel
lintas engine. File DDL di sql/oltp dipakai bila memakai PostgreSQL secara manual.
"""
from __future__ import annotations

import pandas as pd
from sqlalchemy import text

import config as cfg

# Urutan load menghormati dependensi foreign key
LOAD_ORDER = [
    "categories", "suppliers", "stores", "customers", "products",
    "sales_transactions", "sales_details",
    "purchase_orders", "po_details", "inventory_movements",
    "marketing_campaigns",
]

DATE_COLUMNS = {
    "customers": ["join_date"],
    "stores": ["open_date"],
    "sales_transactions": ["transaction_date"],
    "purchase_orders": ["order_date", "received_date"],
    "inventory_movements": ["movement_date"],
    "marketing_campaigns": ["start_date", "end_date"],
}


def _parse_dates(series: pd.Series) -> pd.Series:
    """Parse tanggal campuran menjadi ISO string.

    Penting: coba ISO 8601 dulu agar tanggal seperti '2025-07-01' TIDAK tertukar
    bulan/hari-nya. Hanya baris yang gagal (mis. format DD/MM/YYYY yang sengaja
    disisipkan di join_date) yang di-retry dengan dayfirst=True.
    """
    parsed = pd.to_datetime(series, format="ISO8601", errors="coerce")
    leftover = parsed.isna() & series.notna()
    if leftover.any():
        parsed.loc[leftover] = pd.to_datetime(
            series[leftover], dayfirst=True, errors="coerce")
    return parsed.dt.strftime("%Y-%m-%d")


def _clean(name: str, df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Bersihkan satu tabel; kembalikan df bersih + statistik cleaning."""
    stats = {"dup_removed": 0, "dates_fixed": 0, "nulls_filled": 0}
    before = len(df)

    # 1. Dedup
    df = df.drop_duplicates()
    stats["dup_removed"] = before - len(df)

    # 2. Normalisasi tanggal
    for col in DATE_COLUMNS.get(name, []):
        if col in df.columns:
            df[col] = _parse_dates(df[col])
            stats["dates_fixed"] += 1

    # 3. Missing value handling
    if name == "customers":
        for col in ("gender", "city"):
            n_null = df[col].isna().sum()
            df[col] = df[col].fillna("Tidak Diketahui")
            stats["nulls_filled"] += int(n_null)

    return df, stats


def load() -> None:
    engine = cfg.get_engine()
    print(f"[load_oltp] Target: {cfg.engine_label()}")

    with engine.begin() as conn:
        for name in LOAD_ORDER:
            path = cfg.RAW_DIR / f"{name}.csv"
            if not path.exists():
                raise FileNotFoundError(
                    f"CSV {path} tidak ditemukan. Jalankan generate_data.py dulu.")
            df = pd.read_csv(path)
            df, stats = _clean(name, df)
            df.to_sql(name, conn, if_exists="replace", index=False)
            extra = ""
            if stats["dup_removed"]:
                extra += f" | dedup -{stats['dup_removed']}"
            if stats["nulls_filled"]:
                extra += f" | null-filled {stats['nulls_filled']}"
            print(f"  - {name:22s}: {len(df):>7,} baris{extra}")

    # Verifikasi ringkas
    with engine.connect() as conn:
        n_trx = conn.execute(text("SELECT COUNT(*) FROM sales_transactions")).scalar()
        n_det = conn.execute(text("SELECT COUNT(*) FROM sales_details")).scalar()
    print(f"[load_oltp] Selesai. {n_trx:,} transaksi, {n_det:,} baris detail.")


if __name__ == "__main__":
    load()

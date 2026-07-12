"""
db.py
=====
Utilitas koneksi & query untuk dashboard Streamlit.

Membaca konfigurasi database dari .env di root project (sama dengan ETL):
SQLite default, PostgreSQL opsional. Menyediakan helper query dengan cache
Streamlit agar dashboard responsif.
"""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


@st.cache_resource
def get_engine() -> Engine:
    """SQLAlchemy engine (cached across reruns)."""
    db_engine = os.getenv("DB_ENGINE", "sqlite").lower().strip()
    if db_engine == "postgres":
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB", "umkm_bi")
        user = os.getenv("POSTGRES_USER", "postgres")
        pwd = os.getenv("POSTGRES_PASSWORD", "postgres")
        return create_engine(
            f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}", future=True)
    sqlite_path = os.getenv("SQLITE_PATH", "data/umkm_bi.db")
    abs_path = (PROJECT_ROOT / sqlite_path).resolve()
    return create_engine(f"sqlite:///{abs_path}", future=True)


@st.cache_data(ttl=600)
def run_query(sql: str, params: tuple | None = None) -> pd.DataFrame:
    """Jalankan query SELECT, kembalikan DataFrame (hasil di-cache)."""
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params=params)


def db_ready() -> bool:
    """Cek apakah tabel warehouse sudah tersedia."""
    try:
        run_query("SELECT 1 FROM fact_sales LIMIT 1")
        return True
    except Exception:
        return False


# --------------------------------------------------------------------------- #
# Filter options & WHERE builder (dipakai lintas halaman)
# --------------------------------------------------------------------------- #
@st.cache_data(ttl=600)
def get_filter_options() -> dict:
    stores = run_query("SELECT store_name FROM dim_store ORDER BY store_name")
    channels = run_query("SELECT DISTINCT channel FROM fact_sales ORDER BY channel")
    dates = run_query("SELECT MIN(full_date) AS min_d, MAX(full_date) AS max_d "
                      "FROM dim_date d JOIN fact_sales f ON d.date_key = f.date_key")
    return {
        "stores": stores["store_name"].tolist(),
        "channels": channels["channel"].tolist(),
        "min_date": dates["min_d"].iloc[0],
        "max_date": dates["max_d"].iloc[0],
    }


def build_where(stores: list[str] | None, channels: list[str] | None,
                date_from: str | None, date_to: str | None) -> str:
    """Bangun klausa WHERE dinamis untuk fact_sales (alias f, join dim_store s, dim_date d)."""
    clauses = []
    if stores:
        vals = ", ".join(f"'{s}'" for s in stores)
        clauses.append(f"s.store_name IN ({vals})")
    if channels:
        vals = ", ".join(f"'{c}'" for c in channels)
        clauses.append(f"f.channel IN ({vals})")
    if date_from:
        clauses.append(f"d.full_date >= '{date_from}'")
    if date_to:
        clauses.append(f"d.full_date <= '{date_to}'")
    return ("WHERE " + " AND ".join(clauses)) if clauses else ""


def sidebar_filters(key_prefix: str = "") -> dict:
    """Render filter standar di sidebar & kembalikan pilihannya.

    Dipakai lintas halaman agar konsisten (periode, cabang, channel).
    """
    opts = get_filter_options()
    st.sidebar.header("🔎 Filter")
    date_from = st.sidebar.date_input(
        "Dari tanggal", value=pd.to_datetime(opts["min_date"]),
        key=f"{key_prefix}_from")
    date_to = st.sidebar.date_input(
        "Sampai tanggal", value=pd.to_datetime(opts["max_date"]),
        key=f"{key_prefix}_to")
    stores = st.sidebar.multiselect(
        "Cabang", opts["stores"], default=[], key=f"{key_prefix}_stores",
        help="Kosongkan untuk semua cabang")
    channels = st.sidebar.multiselect(
        "Channel", opts["channels"], default=[], key=f"{key_prefix}_channels",
        help="Kosongkan untuk semua channel")
    return {
        "stores": stores or None,
        "channels": channels or None,
        "date_from": str(date_from),
        "date_to": str(date_to),
        "where": build_where(stores or None, channels or None,
                             str(date_from), str(date_to)),
    }


def rupiah(x: float) -> str:
    """Format angka ke Rupiah ringkas (Rb / Jt / M)."""
    try:
        x = float(x)
    except (TypeError, ValueError):
        return "-"
    if abs(x) >= 1_000_000_000:
        return f"Rp {x/1_000_000_000:.2f} M"
    if abs(x) >= 1_000_000:
        return f"Rp {x/1_000_000:.1f} Jt"
    if abs(x) >= 1_000:
        return f"Rp {x/1_000:.0f} Rb"
    return f"Rp {x:,.0f}"

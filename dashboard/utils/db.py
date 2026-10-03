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


def render_filters(disabled: bool = False) -> dict:
    """Filter standar di sidebar (periode, cabang, channel).

    Dipanggil dari streamlit_app.py supaya pilihan tetap sama saat pindah
    halaman. Halaman yang tidak memakai filter tetap menampilkannya dalam
    keadaan nonaktif agar pilihannya tidak hilang.
    """
    opts = get_filter_options()
    d_min = pd.to_datetime(opts["min_date"]).date()
    d_max = pd.to_datetime(opts["max_date"]).date()

    st.sidebar.markdown('<div class="side-label">Filter</div>', unsafe_allow_html=True)
    rng = st.sidebar.date_input("Periode", value=(d_min, d_max), min_value=d_min,
                                max_value=d_max, format="DD/MM/YYYY",
                                key="flt_periode", disabled=disabled)
    stores = st.sidebar.multiselect("Cabang", opts["stores"], key="flt_cabang",
                                    placeholder="Semua cabang", disabled=disabled)
    channels = st.sidebar.multiselect("Channel", opts["channels"], key="flt_channel",
                                      placeholder="Semua channel", disabled=disabled)
    if disabled:
        st.sidebar.caption("Halaman ini menampilkan kondisi keseluruhan, "
                           "jadi filter tidak dipakai.")

    # Saat pengguna baru memilih tanggal awal, date_input hanya berisi satu nilai.
    if isinstance(rng, (list, tuple)):
        date_from = rng[0] if len(rng) > 0 else d_min
        date_to = rng[1] if len(rng) > 1 else d_max
    else:
        date_from, date_to = rng, d_max

    return {
        "stores": stores or None,
        "channels": channels or None,
        "date_from": str(date_from),
        "date_to": str(date_to),
        "where": build_where(stores or None, channels or None,
                             str(date_from), str(date_to)),
    }


def get_filters() -> dict:
    """Ambil filter yang sudah dirender di streamlit_app.py."""
    return st.session_state["flt"]


def rupiah(x: float) -> str:
    """Dipertahankan untuk kompatibilitas. Gunakan theme.rp untuk kode baru."""
    from utils.theme import rp
    return rp(x)

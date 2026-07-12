"""
config.py
=========
Konfigurasi terpusat untuk seluruh ETL pipeline & dashboard.

Membaca variabel dari file .env (jika ada) dan menyediakan:
  - PROJECT_ROOT, path folder penting
  - get_engine(): SQLAlchemy engine (SQLite default / PostgreSQL opsional)
  - konstanta domain (kota, kategori, brand, channel, dsb.)

Strategi database: PostgreSQL sebagai target utama, SQLite sebagai fallback
default agar proyek langsung dapat dijalankan tanpa instalasi apa pun.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

# --------------------------------------------------------------------------- #
# Path
# --------------------------------------------------------------------------- #
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
SQL_DIR = PROJECT_ROOT / "sql"

# Muat .env dari root project bila tersedia
load_dotenv(PROJECT_ROOT / ".env")

# --------------------------------------------------------------------------- #
# Koneksi database
# --------------------------------------------------------------------------- #
DB_ENGINE = os.getenv("DB_ENGINE", "sqlite").lower().strip()


def get_engine() -> Engine:
    """Kembalikan SQLAlchemy Engine sesuai konfigurasi DB_ENGINE."""
    if DB_ENGINE == "postgres":
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB", "umkm_bi")
        user = os.getenv("POSTGRES_USER", "postgres")
        pwd = os.getenv("POSTGRES_PASSWORD", "postgres")
        url = f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}"
        return create_engine(url, future=True)

    # Default: SQLite (tanpa instalasi)
    sqlite_path = os.getenv("SQLITE_PATH", "data/umkm_bi.db")
    abs_path = (PROJECT_ROOT / sqlite_path).resolve()
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{abs_path}", future=True)


def engine_label() -> str:
    """Label engine aktif untuk logging/tampilan."""
    if DB_ENGINE == "postgres":
        return f"PostgreSQL @ {os.getenv('POSTGRES_HOST', 'localhost')}"
    return f"SQLite ({os.getenv('SQLITE_PATH', 'data/umkm_bi.db')})"


# --------------------------------------------------------------------------- #
# Konstanta domain — konteks UMKM Fashion Indonesia
# --------------------------------------------------------------------------- #
RANDOM_SEED = 42

# Nama brand toko fiktif
COMPANY_NAME = "Rumah Mode Nusantara"

# Cabang toko (nama, kota, provinsi, tipe, tanggal buka)
STORES = [
    ("RMN Jakarta Pusat", "Jakarta", "DKI Jakarta", "flagship", "2019-03-01"),
    ("RMN Bandung Dago", "Bandung", "Jawa Barat", "regular", "2020-06-15"),
    ("RMN Surabaya Tunjungan", "Surabaya", "Jawa Timur", "regular", "2020-11-01"),
    ("RMN Yogyakarta Malioboro", "Yogyakarta", "DI Yogyakarta", "regular", "2021-08-20"),
    ("RMN Medan Sunggal", "Medan", "Sumatera Utara", "regular", "2022-02-10"),
    ("RMN Semarang Simpang Lima", "Semarang", "Jawa Tengah", "regular", "2022-09-05"),
]

# Kota pelanggan (untuk demografi & channel online)
CUSTOMER_CITIES = [
    "Jakarta", "Bandung", "Surabaya", "Yogyakarta", "Medan", "Semarang",
    "Bekasi", "Depok", "Tangerang", "Bogor", "Malang", "Solo", "Denpasar",
]

# Kategori & sub-kategori fashion
CATEGORIES = {
    "Atasan": ["Kemeja", "Kaos", "Blouse", "Sweater"],
    "Bawahan": ["Celana Jeans", "Celana Chino", "Rok", "Celana Kulot"],
    "Dress": ["Dress Casual", "Dress Formal", "Gamis"],
    "Outerwear": ["Jaket", "Hoodie", "Cardigan", "Blazer"],
    "Aksesoris": ["Topi", "Tas", "Ikat Pinggang", "Syal"],
}

# Brand lokal fiktif
BRANDS = ["Senja Label", "Kanaya", "Urban Rakyat", "Bumi Denim",
          "Kirana Wear", "Nusantara Basic", "Rimba Co."]

SIZES = ["S", "M", "L", "XL", "All Size"]
COLORS = ["Hitam", "Putih", "Navy", "Abu-abu", "Krem", "Maroon",
          "Hijau Army", "Coklat", "Biru Muda", "Dusty Pink"]

CHANNELS = ["offline", "shopee", "tokopedia", "instagram"]
CHANNEL_WEIGHTS = [0.50, 0.22, 0.18, 0.10]  # offline masih dominan

PAYMENT_METHODS = ["Tunai", "QRIS", "Kartu Debit", "Kartu Kredit",
                   "Transfer Bank", "GoPay", "OVO", "ShopeePay"]
MEMBER_TIERS = ["Bronze", "Silver", "Gold"]

SUPPLIERS = [
    ("Konveksi Jaya Abadi", "Bandung", 7),
    ("Textile Mandiri", "Solo", 10),
    ("Garmen Sejahtera", "Jakarta", 5),
    ("Denim Works Indonesia", "Bandung", 14),
    ("Aksesoris Kreatif", "Yogyakarta", 6),
]

# Periode data: 12 bulan penuh
DATA_START = "2025-07-01"
DATA_END = "2026-06-30"

# Target volume
# Basis pelanggan dibuat besar (khas retail dgn 20rb transaksi/tahun) agar
# repeat-rate realistis. Distribusi jumlah pembelian diatur di generate_data.py.
N_CUSTOMERS = 12000
N_TRANSACTIONS = 20000

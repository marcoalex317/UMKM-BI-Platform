"""Definisi & Catatan Data: asal data, definisi metrik, batasan, dan pemeriksaan."""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from utils.db import get_filter_options, run_query  # noqa: E402
from utils import theme as t  # noqa: E402

opts = get_filter_options()
t.page_header(
    "Definisi & Catatan Data",
    "Halaman referensi supaya setiap angka di dashboard bisa ditelusuri asalnya.",
    f"Periode data <b>{t.tgl(opts['min_date'])} - {t.tgl(opts['max_date'])}</b>")

# --- Pemeriksaan data -------------------------------------------------------
chk = run_query("""
    SELECT (SELECT SUM(total_amount) FROM sales_transactions) AS oltp,
           (SELECT SUM(net_revenue) FROM fact_sales) AS dwh,
           (SELECT COUNT(*) FROM sales_transactions) AS n_trx,
           (SELECT COUNT(*) FROM fact_sales) AS n_rows
""").iloc[0]
diff = abs(float(chk["oltp"]) - float(chk["dwh"]))
t.kpi_cards([
    ("Revenue di OLTP", t.rp_full(chk["oltp"]), "tabel sales_transactions"),
    ("Revenue di warehouse", t.rp_full(chk["dwh"]), "tabel fact_sales"),
    ("Selisih", t.rp_full(diff), "lolos" if diff < 1 else "perlu dicek"),
    ("Transaksi", t.num(chk["n_trx"]), f"{t.num(chk['n_rows'])} baris item"),
])
t.source("Pipeline membandingkan kedua angka ini setiap kali dijalankan. Selisih nol berarti tidak ada "
         "transaksi yang hilang atau tercatat dua kali saat dipindahkan ke warehouse.")

# --- Model data -------------------------------------------------------------
c1, c2 = st.columns([1.35, 1], gap="large")
with c1:
    t.section("Model data", "Star schema dengan dua tabel fakta yang berbagi dimensi tanggal, produk, dan cabang.")
    st.image(str(HERE / "assets" / "star_schema.svg"), width="stretch")
with c2:
    t.section("Asal data")
    st.markdown(
        f"""
<div class="note" style="margin-top:0.4rem">
<ul>
<li>Rumah Mode Nusantara adalah toko fiktif. Datanya saya bangkitkan dengan Python (Faker, seed 42),
jadi angkanya selalu sama setiap pipeline dijalankan.</li>
<li>Pola musiman seperti Ramadan, Lebaran, dan Harbolnas sengaja dimasukkan ke generator.</li>
<li>Alurnya: CSV mentah, database transaksional (OLTP), lalu data warehouse. Dashboard membaca dari warehouse.</li>
<li>Database default SQLite, bisa diganti PostgreSQL lewat file <code>.env</code>.</li>
</ul>
</div>
""", unsafe_allow_html=True)

# --- Definisi metrik --------------------------------------------------------
t.section("Definisi metrik")
defs = pd.DataFrame([
    ("Revenue", "Penjualan bersih setelah diskon.", "SUM(net_revenue)"),
    ("Gross profit", "Revenue dikurangi harga pokok barang yang terjual.", "SUM(net_revenue - cost)"),
    ("Margin riil", "Gross profit dibagi revenue, sesudah diskon.", "gross profit / revenue"),
    ("Margin harga jual", "Selisih harga jual dan harga pokok sebelum diskon.", "dim_product.margin_pct"),
    ("Rata-rata transaksi", "Nilai rata-rata satu struk.", "revenue / jumlah transaksi"),
    ("Repeat rate", "Porsi member yang belanja lebih dari sekali dalam periode.", "member dengan > 1 transaksi / member aktif"),
    ("Porsi online", "Revenue dari Shopee, Tokopedia, dan Instagram.", "channel <> 'offline'"),
    ("Nilai stok", "Stok terakhir per produk per cabang dikali harga pokok.", "stock_on_hand x cost_price"),
    ("Cukup untuk", "Perkiraan berapa bulan stok bertahan.", "stok / rata-rata jual per bulan"),
], columns=["Metrik", "Arti", "Cara hitung"])
st.dataframe(defs, hide_index=True, width="stretch")

# --- Batas dan aturan -------------------------------------------------------
c3, c4 = st.columns(2, gap="large")
with c3:
    t.section("Batas yang saya tentukan sendiri",
              "Angka-angka ini pilihan analis, bukan standar baku. Bisa diubah di kode halaman.")
    st.dataframe(pd.DataFrame([
        ("Dead stock", "Terjual 5 unit atau kurang dalam setahun"),
        ("Margin tipis", "Margin harga jual di bawah 25%"),
        ("Restock urgent", "Stok cukup untuk kurang dari 1 bulan"),
        ("Restock segera", "Stok cukup untuk 1 sampai 2 bulan"),
        ("Ikut daftar restock", "Terjual lebih dari 2 unit per bulan"),
    ], columns=["Aturan", "Batas"]), hide_index=True, width="stretch")
with c4:
    t.section("Segmen pelanggan", "Versi sederhana dari RFM, memakai frekuensi dan total belanja setahun.")
    st.dataframe(pd.DataFrame([
        ("Champion", "4 transaksi atau lebih dan belanja minimal Rp 1 juta"),
        ("Loyal", "2 transaksi atau lebih"),
        ("Big spender", "1 transaksi dengan belanja minimal Rp 1 juta"),
        ("Occasional", "1 transaksi di bawah Rp 1 juta"),
    ], columns=["Segmen", "Aturan"]), hide_index=True, width="stretch")

# --- Keterbatasan -----------------------------------------------------------
t.note([
    "Datanya sintetis. Dashboard ini menunjukkan cara analisis, bukan kondisi toko sungguhan.",
    "Tidak ada biaya operasional cabang (sewa, gaji, listrik), jadi analisis berhenti di gross profit.",
    "Sekitar 10% revenue berasal dari pembeli non-member, sehingga halaman Pelanggan hanya mencakup member.",
    "Tidak ada catatan stok habis, jadi penjualan yang hilang karena kehabisan barang tidak terhitung.",
    "Halaman Inventori dan Pelanggan tidak mengikuti filter karena menggambarkan kondisi keseluruhan.",
], title="Keterbatasan")

"""
streamlit_app.py - Landing page dashboard BI "Rumah Mode Nusantara".

Jalankan dari root project:
    streamlit run dashboard/streamlit_app.py

Halaman analitik ada di folder pages/ (otomatis muncul di sidebar).
"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils.db import db_ready, run_query, rupiah  # noqa: E402

st.set_page_config(page_title="Rumah Mode Nusantara - BI Platform",
                   page_icon="📊", layout="wide")

st.title("📊 Rumah Mode Nusantara - Business Intelligence Platform")
st.caption("End-to-End Retail BI untuk UMKM Fashion Indonesia")

if not db_ready():
    st.error(
        "❌ Data warehouse belum tersedia.\n\n"
        "Jalankan ETL pipeline terlebih dahulu:\n\n"
        "```\npip install -r requirements.txt\npython etl/run_pipeline.py\n```")
    st.stop()

# Ringkasan tingkat tinggi
kpi = run_query("""
    SELECT SUM(net_revenue) AS revenue,
           SUM(gross_profit) AS profit,
           COUNT(DISTINCT transaction_id) AS n_trx,
           COUNT(DISTINCT customer_key) AS n_cust
    FROM fact_sales
""").iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Revenue", rupiah(kpi["revenue"]))
c2.metric("Gross Profit", rupiah(kpi["profit"]))
c3.metric("Transaksi", f"{int(kpi['n_trx']):,}")
c4.metric("Pelanggan Aktif", f"{int(kpi['n_cust']):,}")

st.divider()

st.markdown("""
### Selamat datang 👋
Platform ini menganalisis penjualan, produk, inventori, pelanggan, dan cabang
dari chain fashion UMKM **Rumah Mode Nusantara**. Gunakan menu di sidebar untuk
menjelajahi 6 halaman analitik:

| Halaman | Fokus |
|---------|-------|
| **1 · Executive Overview** | KPI utama, tren revenue, kontribusi kategori |
| **2 · Sales Performance** | Tren penjualan, channel, metode pembayaran |
| **3 · Product & Category** | Best seller, margin, analisis size & warna |
| **4 · Inventory & Restock** | Stok, dead stock, rekomendasi restock |
| **5 · Customer Analysis** | Repeat rate, member tier, RFM, demografi |
| **6 · Branch Performance** | Perbandingan & ranking cabang |

**Tech stack:** PostgreSQL/SQLite · Python ETL · Star Schema DWH · Streamlit + Plotly
""")

st.info("💡 Setiap halaman punya filter di sidebar (periode, cabang, channel) "
        "dan menampilkan insight bisnis siap-aksi untuk owner UMKM.")

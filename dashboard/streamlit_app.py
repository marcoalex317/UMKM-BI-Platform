"""
streamlit_app.py
================
Titik masuk dashboard Rumah Mode Nusantara.

Jalankan dari root project:
    streamlit run dashboard/streamlit_app.py

File ini mengatur tema, logo, menu halaman, dan filter di sidebar. Isi tiap
halaman ada di folder pages/.
"""
import sys
from pathlib import Path

import streamlit as st

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from utils.db import db_ready, get_filter_options, render_filters  # noqa: E402
from utils.theme import apply_theme, tgl  # noqa: E402

st.set_page_config(page_title="Rumah Mode Nusantara | Retail Analytics",
                   layout="wide", initial_sidebar_state="expanded")
apply_theme()
st.logo(str(HERE / "assets" / "logo.svg"), size="large")

if not db_ready():
    st.error("Data warehouse belum tersedia. Jalankan ETL pipeline terlebih dahulu:\n\n"
             "```\npip install -r requirements.txt\npython etl/run_pipeline.py\n```")
    st.stop()

overview = st.Page("pages/1_Executive_Overview.py", title="Executive Overview", default=True)
sales = st.Page("pages/2_Sales_Performance.py", title="Sales Performance", url_path="sales")
product = st.Page("pages/3_Product_Category.py", title="Produk & Kategori", url_path="produk")
inventory = st.Page("pages/4_Inventory_Restock.py", title="Inventori & Restock", url_path="inventori")
customer = st.Page("pages/5_Customer_Analysis.py", title="Pelanggan", url_path="pelanggan")
branch = st.Page("pages/6_Branch_Performance.py", title="Kinerja Cabang", url_path="cabang")
notes = st.Page("pages/7_Catatan_Data.py", title="Definisi & Catatan Data", url_path="catatan")

pg = st.navigation({
    "Ringkasan": [overview],
    "Analisis": [sales, product, inventory, customer, branch],
    "Referensi": [notes],
})

uses_filter = pg.title in {overview.title, sales.title, product.title, branch.title}
st.session_state["flt"] = render_filters(disabled=not uses_filter)

opts = get_filter_options()
st.sidebar.markdown(
    '<div class="side-foot">Data transaksi '
    f'{tgl(opts["min_date"])} s.d. {tgl(opts["max_date"])}<br>'
    'Sumber: data warehouse umkm_bi<br>'
    'Disusun oleh Marco Alexander</div>',
    unsafe_allow_html=True)

pg.run()

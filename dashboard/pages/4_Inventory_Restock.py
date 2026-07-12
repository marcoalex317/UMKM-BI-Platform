"""Halaman 4 — Inventory & Restock: stok, dead stock, rekomendasi restock."""
import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.db import run_query, rupiah  # noqa: E402

st.set_page_config(page_title="Inventory & Restock", page_icon="📦", layout="wide")
st.title("📦 Inventory & Restock")
st.caption("Analisis stok berbasis seluruh cabang (level warehouse).")

# Stok terkini per produk (baris terakhir per produk & toko, dijumlah)
STOCK_CTE = """
WITH stock AS (
    SELECT product_key, SUM(stock_on_hand) AS stock_now
    FROM (
        SELECT product_key, store_key, stock_on_hand,
               ROW_NUMBER() OVER (PARTITION BY product_key, store_key
                                  ORDER BY date_key DESC) AS rn
        FROM fact_inventory
    ) t WHERE rn = 1
    GROUP BY product_key
),
sold AS (
    SELECT product_key, SUM(quantity) AS qty_sold, SUM(quantity)/12.0 AS avg_month
    FROM fact_sales GROUP BY product_key
)
"""

# --- KPI ---
kpi = run_query(STOCK_CTE + """
    SELECT SUM(s.stock_now) AS total_unit,
           SUM(s.stock_now * p.cost_price) AS nilai_stok
    FROM stock s JOIN dim_product p ON s.product_key = p.product_key
""").iloc[0]
low = run_query(STOCK_CTE + """
    SELECT COUNT(*) AS n FROM stock s
    JOIN sold so ON s.product_key = so.product_key
    WHERE so.avg_month > 2 AND s.stock_now / NULLIF(so.avg_month,0) < 1
""").iloc[0]["n"]
dead = run_query(STOCK_CTE + """
    SELECT COUNT(*) AS n FROM dim_product p
    LEFT JOIN sold so ON p.product_key = so.product_key
    WHERE COALESCE(so.qty_sold,0) <= 5
""").iloc[0]["n"]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Unit Stok", f"{int(kpi['total_unit'] or 0):,}")
c2.metric("Nilai Inventori", rupiah(kpi["nilai_stok"] or 0))
c3.metric("Produk Low Stock", f"{int(low)}", help="Stok < 1 bulan penjualan")
c4.metric("Dead / Slow Stock", f"{int(dead)}", help="Terjual ≤ 5 unit / tahun")
st.divider()

# --- Rekomendasi restock ---
st.subheader("🔴 Rekomendasi Restock (prioritas)")
restock = run_query(STOCK_CTE + """
    SELECT p.product_name, p.category, p.brand,
           ROUND(so.avg_month,1) AS jual_per_bulan,
           s.stock_now AS stok,
           ROUND(s.stock_now / NULLIF(so.avg_month,0),1) AS bulan_tersisa,
           CASE
             WHEN s.stock_now / NULLIF(so.avg_month,0) < 1 THEN '🔴 URGENT'
             WHEN s.stock_now / NULLIF(so.avg_month,0) < 2 THEN '🟠 Segera'
             ELSE '🟢 Aman' END AS status
    FROM stock s
    JOIN sold so ON s.product_key = so.product_key
    JOIN dim_product p ON s.product_key = p.product_key
    WHERE so.avg_month > 2
    ORDER BY bulan_tersisa ASC LIMIT 15
""")
st.dataframe(restock.rename(columns={
    "product_name": "Produk", "category": "Kategori", "brand": "Brand",
    "jual_per_bulan": "Jual/Bln", "stok": "Stok", "bulan_tersisa": "Bulan Tersisa",
    "status": "Status"}), width='stretch', hide_index=True)

# --- Dead stock ---
col1, col2 = st.columns([1, 1])
with col1:
    st.subheader("⚠️ Dead / Slow Moving Stock")
    ds = run_query(STOCK_CTE + """
        SELECT p.product_name, p.category, COALESCE(so.qty_sold,0) AS terjual,
               COALESCE(s.stock_now,0) AS stok,
               COALESCE(s.stock_now,0) * p.cost_price AS nilai_mengendap
        FROM dim_product p
        LEFT JOIN sold so ON p.product_key = so.product_key
        LEFT JOIN stock s ON p.product_key = s.product_key
        WHERE COALESCE(so.qty_sold,0) <= 5
        ORDER BY nilai_mengendap DESC LIMIT 15
    """)
    ds_disp = ds.copy()
    ds_disp["nilai_mengendap"] = ds_disp["nilai_mengendap"].apply(rupiah)
    st.dataframe(ds_disp.rename(columns={
        "product_name": "Produk", "category": "Kategori", "terjual": "Terjual/thn",
        "stok": "Stok", "nilai_mengendap": "Modal Mengendap"}),
        width='stretch', hide_index=True)
with col2:
    st.subheader("Nilai Stok per Kategori")
    val = run_query(STOCK_CTE + """
        SELECT p.parent_category AS kategori,
               SUM(s.stock_now * p.cost_price) AS nilai
        FROM stock s JOIN dim_product p ON s.product_key = p.product_key
        GROUP BY p.parent_category ORDER BY nilai DESC
    """)
    st.plotly_chart(px.bar(val, x="kategori", y="nilai", color="kategori",
                           labels={"nilai": "Nilai Stok (Rp)", "kategori": ""})
                    .update_layout(showlegend=False, height=380), width='stretch')

dead_val = ds["nilai_mengendap"].sum() if len(ds) else 0
st.warning(f"💡 **Insight:** Sekitar **{int(dead)} SKU** tergolong dead/slow stock dengan "
           f"modal mengendap ~**{rupiah(dead_val)}**. Pertimbangkan clearance sale, bundling, "
           f"atau stop restock. Sementara **{int(low)} produk** butuh restock segera agar "
           f"tidak kehilangan penjualan.")

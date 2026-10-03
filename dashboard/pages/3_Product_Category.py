"""Halaman 3 - Product & Category Analysis: best seller, margin, size/warna."""
import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.db import run_query, sidebar_filters, rupiah  # noqa: E402

st.set_page_config(page_title="Product & Category", page_icon="👕", layout="wide")
st.title("👕 Product & Category Analysis")

f = sidebar_filters("prod")
where = f["where"]

# --- Best sellers ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("🏆 Top 10 Produk Terlaris (unit)")
    top = run_query(f"""
        SELECT p.product_name, p.category, SUM(f.quantity) AS qty,
               SUM(f.net_revenue) AS revenue
        FROM fact_sales f
        JOIN dim_product p ON f.product_key = p.product_key
        JOIN dim_store s ON f.store_key = s.store_key
        JOIN dim_date d ON f.date_key = d.date_key {where}
        GROUP BY p.product_name, p.category
        ORDER BY qty DESC LIMIT 10
    """)
    st.plotly_chart(px.bar(top, x="qty", y="product_name", orientation="h",
                           color="qty", color_continuous_scale="Greens",
                           labels={"qty": "Unit", "product_name": ""})
                    .update_layout(height=380, yaxis={"categoryorder": "total ascending"}),
                    width='stretch')
with col2:
    st.subheader("💰 Top 10 Produk Margin Tertinggi")
    marg = run_query(f"""
        SELECT p.product_name, p.margin_pct, SUM(f.gross_profit) AS profit
        FROM fact_sales f
        JOIN dim_product p ON f.product_key = p.product_key
        JOIN dim_store s ON f.store_key = s.store_key
        JOIN dim_date d ON f.date_key = d.date_key {where}
        GROUP BY p.product_name, p.margin_pct
        HAVING SUM(f.quantity) > 0
        ORDER BY p.margin_pct DESC LIMIT 10
    """)
    st.plotly_chart(px.bar(marg, x="margin_pct", y="product_name", orientation="h",
                           color="margin_pct", color_continuous_scale="Purples",
                           labels={"margin_pct": "Margin %", "product_name": ""})
                    .update_layout(height=380, yaxis={"categoryorder": "total ascending"}),
                    width='stretch')

st.divider()

# --- Pareto kategori ---
st.subheader("Analisis Kategori (Pareto 80/20)")
cat = run_query(f"""
    SELECT p.category, SUM(f.net_revenue) AS revenue, SUM(f.gross_profit) AS profit
    FROM fact_sales f
    JOIN dim_product p ON f.product_key = p.product_key
    JOIN dim_store s ON f.store_key = s.store_key
    JOIN dim_date d ON f.date_key = d.date_key {where}
    GROUP BY p.category ORDER BY revenue DESC
""")
cat["cum_pct"] = cat["revenue"].cumsum() / cat["revenue"].sum() * 100
fig = px.bar(cat, x="category", y="revenue", labels={"category": "", "revenue": "Revenue"})
fig.add_scatter(x=cat["category"], y=cat["cum_pct"] / 100 * cat["revenue"].max(),
                mode="lines+markers", name="Kumulatif %", yaxis="y")
fig.update_layout(height=360, showlegend=False)
st.plotly_chart(fig, width='stretch')

# --- Size & color analysis (khas fashion) ---
col3, col4 = st.columns(2)
with col3:
    st.subheader("Penjualan per Ukuran")
    size = run_query(f"""
        SELECT p.size, SUM(f.quantity) AS qty
        FROM fact_sales f
        JOIN dim_product p ON f.product_key = p.product_key
        JOIN dim_store s ON f.store_key = s.store_key
        JOIN dim_date d ON f.date_key = d.date_key {where}
        GROUP BY p.size ORDER BY qty DESC
    """)
    st.plotly_chart(px.bar(size, x="size", y="qty", color="size")
                    .update_layout(showlegend=False, height=300), width='stretch')
with col4:
    st.subheader("Penjualan per Warna")
    color = run_query(f"""
        SELECT p.color, SUM(f.quantity) AS qty
        FROM fact_sales f
        JOIN dim_product p ON f.product_key = p.product_key
        JOIN dim_store s ON f.store_key = s.store_key
        JOIN dim_date d ON f.date_key = d.date_key {where}
        GROUP BY p.color ORDER BY qty DESC LIMIT 10
    """)
    st.plotly_chart(px.bar(color, x="qty", y="color", orientation="h", color="qty",
                           color_continuous_scale="Oranges", labels={"color": "", "qty": "Unit"})
                    .update_layout(height=300, yaxis={"categoryorder": "total ascending"}),
                    width='stretch')

top_name = top.iloc[0]["product_name"] if len(top) else "-"
st.success(f"💡 **Insight:** Produk terlaris **{top_name}**. Ukuran & warna terlaris "
           f"perlu diprioritaskan saat restock. Produk margin tinggi bisa didorong lewat "
           f"bundling dengan best-seller untuk mengangkat profit total.")

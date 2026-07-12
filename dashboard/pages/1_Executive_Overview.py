"""Halaman 1 — Executive Overview: KPI utama untuk owner UMKM."""
import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.db import run_query, sidebar_filters, rupiah  # noqa: E402

st.set_page_config(page_title="Executive Overview", page_icon="📈", layout="wide")
st.title("📈 Executive Overview")

f = sidebar_filters("exec")
where = f["where"]

# --- KPI cards ---
kpi = run_query(f"""
    SELECT SUM(f.net_revenue) AS revenue,
           SUM(f.gross_profit) AS profit,
           COUNT(DISTINCT f.transaction_id) AS n_trx,
           SUM(f.quantity) AS qty,
           COUNT(DISTINCT f.customer_key) AS n_cust
    FROM fact_sales f
    JOIN dim_store s ON f.store_key = s.store_key
    JOIN dim_date d ON f.date_key = d.date_key
    {where}
""").iloc[0]

revenue = kpi["revenue"] or 0
profit = kpi["profit"] or 0
n_trx = int(kpi["n_trx"] or 0)
margin = (profit / revenue * 100) if revenue else 0
aov = (revenue / n_trx) if n_trx else 0

# repeat rate
rr = run_query(f"""
    WITH per_cust AS (
        SELECT f.customer_key, COUNT(DISTINCT f.transaction_id) AS n
        FROM fact_sales f
        JOIN dim_store s ON f.store_key = s.store_key
        JOIN dim_date d ON f.date_key = d.date_key
        {where} {'AND' if where else 'WHERE'} f.customer_key IS NOT NULL
        GROUP BY f.customer_key
    )
    SELECT ROUND(100.0 * SUM(CASE WHEN n>1 THEN 1 ELSE 0 END)/COUNT(*),1) AS rate
    FROM per_cust
""").iloc[0]["rate"]

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Revenue", rupiah(revenue))
c2.metric("Gross Profit", rupiah(profit))
c3.metric("Margin", f"{margin:.1f}%")
c4.metric("Avg Order Value", rupiah(aov))
c5.metric("Repeat Rate", f"{rr or 0:.1f}%")

st.divider()

# --- Tren revenue bulanan ---
col1, col2 = st.columns([2, 1])
with col1:
    st.subheader("Tren Revenue & Profit Bulanan")
    trend = run_query(f"""
        SELECT d.year, d.month, d.month_name,
               SUM(f.net_revenue) AS revenue, SUM(f.gross_profit) AS profit
        FROM fact_sales f
        JOIN dim_store s ON f.store_key = s.store_key
        JOIN dim_date d ON f.date_key = d.date_key
        {where}
        GROUP BY d.year, d.month, d.month_name
        ORDER BY d.year, d.month
    """)
    trend["periode"] = trend["month_name"].str[:3] + " " + trend["year"].astype(str)
    fig = px.line(trend, x="periode", y=["revenue", "profit"], markers=True,
                  labels={"value": "Rupiah", "periode": "", "variable": ""})
    fig.update_layout(legend_title="", height=380)
    st.plotly_chart(fig, width='stretch')

with col2:
    st.subheader("Kontribusi Kategori")
    cat = run_query(f"""
        SELECT p.parent_category AS kategori, SUM(f.net_revenue) AS revenue
        FROM fact_sales f
        JOIN dim_product p ON f.product_key = p.product_key
        JOIN dim_store s ON f.store_key = s.store_key
        JOIN dim_date d ON f.date_key = d.date_key
        {where}
        GROUP BY p.parent_category
        ORDER BY revenue DESC
    """)
    fig2 = px.pie(cat, names="kategori", values="revenue", hole=0.45)
    fig2.update_layout(height=380)
    st.plotly_chart(fig2, width='stretch')

# --- Revenue per channel & cabang ---
col3, col4 = st.columns(2)
with col3:
    st.subheader("Revenue per Channel")
    ch = run_query(f"""
        SELECT f.channel, SUM(f.net_revenue) AS revenue
        FROM fact_sales f
        JOIN dim_store s ON f.store_key = s.store_key
        JOIN dim_date d ON f.date_key = d.date_key
        {where}
        GROUP BY f.channel ORDER BY revenue DESC
    """)
    st.plotly_chart(px.bar(ch, x="channel", y="revenue",
                           color="channel").update_layout(showlegend=False, height=320),
                    width='stretch')
with col4:
    st.subheader("Revenue per Cabang")
    br = run_query(f"""
        SELECT s.store_name, SUM(f.net_revenue) AS revenue
        FROM fact_sales f
        JOIN dim_store s ON f.store_key = s.store_key
        JOIN dim_date d ON f.date_key = d.date_key
        {where}
        GROUP BY s.store_name ORDER BY revenue DESC
    """)
    st.plotly_chart(px.bar(br, x="revenue", y="store_name", orientation="h",
                           color="revenue", color_continuous_scale="Blues")
                    .update_layout(height=320, yaxis={"categoryorder": "total ascending"}),
                    width='stretch')

st.success(f"💡 **Insight:** Margin rata-rata **{margin:.1f}%** dengan repeat rate "
           f"**{rr or 0:.1f}%**. Fokuskan promosi pada bulan puncak (Ramadan & Harbolnas) "
           f"dan kategori kontributor revenue terbesar.")

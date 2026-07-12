"""Halaman 6 — Branch/Store Performance: perbandingan & ranking cabang."""
import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.db import run_query, sidebar_filters, rupiah  # noqa: E402

st.set_page_config(page_title="Branch Performance", page_icon="🏬", layout="wide")
st.title("🏬 Branch / Store Performance")

f = sidebar_filters("branch")
where = f["where"]

# --- Ranking cabang ---
st.subheader("Ranking Cabang")
rank = run_query(f"""
    SELECT s.store_name, s.city, s.store_type,
           COUNT(DISTINCT f.transaction_id) AS n_trx,
           SUM(f.net_revenue) AS revenue,
           SUM(f.gross_profit) AS profit,
           ROUND(SUM(f.net_revenue)*1.0/COUNT(DISTINCT f.transaction_id),0) AS aov,
           ROUND(100.0*SUM(f.gross_profit)/NULLIF(SUM(f.net_revenue),0),1) AS margin_pct
    FROM fact_sales f
    JOIN dim_store s ON f.store_key = s.store_key
    JOIN dim_date d ON f.date_key = d.date_key {where}
    GROUP BY s.store_name, s.city, s.store_type
    ORDER BY revenue DESC
""")

col1, col2 = st.columns([1.3, 1])
with col1:
    st.plotly_chart(px.bar(rank, x="revenue", y="store_name", orientation="h",
                           color="revenue", color_continuous_scale="Blues",
                           labels={"revenue": "Revenue", "store_name": ""})
                    .update_layout(height=380, yaxis={"categoryorder": "total ascending"}),
                    width='stretch')
with col2:
    disp = rank.copy()
    disp["revenue"] = disp["revenue"].apply(rupiah)
    disp["profit"] = disp["profit"].apply(rupiah)
    disp["aov"] = disp["aov"].apply(rupiah)
    st.dataframe(disp.rename(columns={"store_name": "Cabang", "city": "Kota",
                 "store_type": "Tipe", "n_trx": "Trx", "revenue": "Revenue",
                 "profit": "Profit", "aov": "AOV", "margin_pct": "Margin%"}),
                 width='stretch', hide_index=True)

st.divider()

# --- Channel mix per cabang ---
col3, col4 = st.columns(2)
with col3:
    st.subheader("Channel Mix per Cabang")
    mix = run_query(f"""
        SELECT s.store_name, f.channel, SUM(f.net_revenue) AS revenue
        FROM fact_sales f
        JOIN dim_store s ON f.store_key = s.store_key
        JOIN dim_date d ON f.date_key = d.date_key {where}
        GROUP BY s.store_name, f.channel
    """)
    st.plotly_chart(px.bar(mix, x="store_name", y="revenue", color="channel",
                           labels={"store_name": "", "revenue": "Revenue"})
                    .update_layout(height=360, barmode="stack",
                                   xaxis={"tickangle": -30}), width='stretch')
with col4:
    st.subheader("Tren Bulanan per Cabang")
    trend = run_query(f"""
        SELECT s.store_name, d.year, d.month, d.month_name,
               SUM(f.net_revenue) AS revenue
        FROM fact_sales f
        JOIN dim_store s ON f.store_key = s.store_key
        JOIN dim_date d ON f.date_key = d.date_key {where}
        GROUP BY s.store_name, d.year, d.month, d.month_name
        ORDER BY d.year, d.month
    """)
    trend["periode"] = trend["month_name"].str[:3] + " " + trend["year"].astype(str)
    st.plotly_chart(px.line(trend, x="periode", y="revenue", color="store_name",
                            labels={"periode": "", "revenue": "Revenue", "store_name": "Cabang"})
                    .update_layout(height=360), width='stretch')

if len(rank):
    best = rank.iloc[0]
    worst = rank.iloc[-1]
    gap = best["revenue"] / worst["revenue"] if worst["revenue"] else 0
    st.success(
        f"💡 **Insight:** Cabang terbaik **{best['store_name']}** "
        f"({rupiah(best['revenue'])}) vs terlemah **{worst['store_name']}** "
        f"({rupiah(worst['revenue'])}) — selisih ~**{gap:.1f}x**. "
        f"Evaluasi cabang berperforma rendah: lokasi, staf, stok, atau dorong "
        f"channel online untuk menaikkan jangkauan.")

"""Halaman 2 — Sales Performance: tren penjualan, channel, pembayaran."""
import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.db import run_query, sidebar_filters, rupiah  # noqa: E402

st.set_page_config(page_title="Sales Performance", page_icon="🛍️", layout="wide")
st.title("🛍️ Sales Performance")

f = sidebar_filters("sales")
where = f["where"]

# --- KPI ringkas ---
k = run_query(f"""
    SELECT SUM(f.net_revenue) AS revenue, SUM(f.quantity) AS qty,
           COUNT(DISTINCT f.transaction_id) AS n_trx
    FROM fact_sales f
    JOIN dim_store s ON f.store_key = s.store_key
    JOIN dim_date d ON f.date_key = d.date_key {where}
""").iloc[0]
c1, c2, c3 = st.columns(3)
c1.metric("Revenue", rupiah(k["revenue"] or 0))
c2.metric("Unit Terjual", f"{int(k['qty'] or 0):,}")
c3.metric("Transaksi", f"{int(k['n_trx'] or 0):,}")
st.divider()

# --- Tren harian ---
st.subheader("Tren Revenue Harian")
daily = run_query(f"""
    SELECT d.full_date, SUM(f.net_revenue) AS revenue
    FROM fact_sales f
    JOIN dim_store s ON f.store_key = s.store_key
    JOIN dim_date d ON f.date_key = d.date_key {where}
    GROUP BY d.full_date ORDER BY d.full_date
""")
st.plotly_chart(px.area(daily, x="full_date", y="revenue",
                        labels={"full_date": "", "revenue": "Revenue"})
                .update_layout(height=330), width='stretch')

# --- Channel & payment ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("Performa per Channel")
    ch = run_query(f"""
        SELECT f.channel,
               SUM(f.net_revenue) AS revenue,
               COUNT(DISTINCT f.transaction_id) AS n_trx,
               ROUND(SUM(f.net_revenue)*1.0/COUNT(DISTINCT f.transaction_id),0) AS aov
        FROM fact_sales f
        JOIN dim_store s ON f.store_key = s.store_key
        JOIN dim_date d ON f.date_key = d.date_key {where}
        GROUP BY f.channel ORDER BY revenue DESC
    """)
    st.plotly_chart(px.bar(ch, x="channel", y="revenue", color="channel",
                           text_auto=".2s").update_layout(showlegend=False, height=300),
                    width='stretch')
    ch["revenue"] = ch["revenue"].apply(rupiah)
    ch["aov"] = ch["aov"].apply(rupiah)
    st.dataframe(ch.rename(columns={"channel": "Channel", "revenue": "Revenue",
                 "n_trx": "Transaksi", "aov": "AOV"}), width='stretch', hide_index=True)
with col2:
    st.subheader("Metode Pembayaran")
    pay = run_query(f"""
        SELECT st.payment_method, SUM(f.net_revenue) AS revenue
        FROM fact_sales f
        JOIN sales_transactions st ON f.transaction_id = st.transaction_id
        JOIN dim_store s ON f.store_key = s.store_key
        JOIN dim_date d ON f.date_key = d.date_key {where}
        GROUP BY st.payment_method ORDER BY revenue DESC
    """)
    st.plotly_chart(px.pie(pay, names="payment_method", values="revenue", hole=0.4)
                    .update_layout(height=300), width='stretch')

# --- Weekday vs weekend ---
st.subheader("Pola Penjualan: Hari dalam Seminggu")
dow = run_query(f"""
    SELECT d.day_of_week, d.day_name, SUM(f.net_revenue) AS revenue
    FROM fact_sales f
    JOIN dim_store s ON f.store_key = s.store_key
    JOIN dim_date d ON f.date_key = d.date_key {where}
    GROUP BY d.day_of_week, d.day_name ORDER BY d.day_of_week
""")
st.plotly_chart(px.bar(dow, x="day_name", y="revenue", color="revenue",
                       color_continuous_scale="Teal", labels={"day_name": "", "revenue": "Revenue"})
                .update_layout(height=300), width='stretch')

best_ch = ch.iloc[0]["channel"] if len(ch) else "-"
st.success(f"💡 **Insight:** Channel **{best_ch}** menyumbang revenue tertinggi. "
           f"Penjualan cenderung naik di akhir pekan — pertimbangkan promo weekend "
           f"dan penguatan stok jelang musim ramai.")

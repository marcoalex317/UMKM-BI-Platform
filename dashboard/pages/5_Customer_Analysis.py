"""Halaman 5 — Customer Analysis: repeat rate, tier, RFM sederhana, demografi."""
import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.db import run_query, rupiah  # noqa: E402

st.set_page_config(page_title="Customer Analysis", page_icon="🧑‍🤝‍🧑", layout="wide")
st.title("🧑‍🤝‍🧑 Customer Analysis")

# --- KPI ---
base = run_query("""
    WITH per_cust AS (
        SELECT customer_key,
               COUNT(DISTINCT transaction_id) AS n_trx,
               SUM(net_revenue) AS spend
        FROM fact_sales WHERE customer_key IS NOT NULL
        GROUP BY customer_key
    )
    SELECT COUNT(*) AS total,
           SUM(CASE WHEN n_trx>1 THEN 1 ELSE 0 END) AS repeat_cust,
           AVG(spend) AS avg_spend,
           AVG(n_trx) AS avg_freq
    FROM per_cust
""").iloc[0]
total = int(base["total"] or 0)
repeat = int(base["repeat_cust"] or 0)
rate = (repeat / total * 100) if total else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Pelanggan Aktif", f"{total:,}")
c2.metric("Repeat Customer", f"{repeat:,}")
c3.metric("Repeat Rate", f"{rate:.1f}%")
c4.metric("Avg Spend / Cust", rupiah(base["avg_spend"] or 0))
st.divider()

col1, col2 = st.columns(2)
with col1:
    st.subheader("Revenue per Member Tier")
    tier = run_query("""
        SELECT c.member_tier, SUM(f.net_revenue) AS revenue,
               COUNT(DISTINCT c.customer_key) AS n_cust
        FROM fact_sales f
        JOIN dim_customer c ON f.customer_key = c.customer_key
        GROUP BY c.member_tier
        ORDER BY CASE c.member_tier WHEN 'Gold' THEN 1 WHEN 'Silver' THEN 2 ELSE 3 END
    """)
    st.plotly_chart(px.bar(tier, x="member_tier", y="revenue", color="member_tier",
                           color_discrete_map={"Gold": "#D4AF37", "Silver": "#A9A9A9",
                                               "Bronze": "#CD7F32"},
                           labels={"member_tier": "", "revenue": "Revenue"})
                    .update_layout(showlegend=False, height=330), width='stretch')
with col2:
    st.subheader("Segmentasi RFM Sederhana")
    rfm = run_query("""
        WITH per_cust AS (
            SELECT customer_key,
                   COUNT(DISTINCT transaction_id) AS frequency,
                   SUM(net_revenue) AS monetary
            FROM fact_sales WHERE customer_key IS NOT NULL
            GROUP BY customer_key
        )
        SELECT
            CASE
              WHEN frequency >= 4 AND monetary >= 1000000 THEN 'Champion'
              WHEN frequency >= 2 THEN 'Loyal'
              WHEN monetary >= 1000000 THEN 'Big Spender'
              ELSE 'Occasional' END AS segmen,
            COUNT(*) AS n_cust, SUM(monetary) AS revenue
        FROM per_cust GROUP BY segmen ORDER BY revenue DESC
    """)
    st.plotly_chart(px.pie(rfm, names="segmen", values="revenue", hole=0.4)
                    .update_layout(height=330), width='stretch')

# --- Demografi ---
col3, col4 = st.columns(2)
with col3:
    st.subheader("Demografi: Kelompok Usia")
    age = run_query("""
        SELECT c.age_group, SUM(f.net_revenue) AS revenue
        FROM fact_sales f JOIN dim_customer c ON f.customer_key = c.customer_key
        GROUP BY c.age_group ORDER BY c.age_group
    """)
    st.plotly_chart(px.bar(age, x="age_group", y="revenue", color="revenue",
                           color_continuous_scale="Blues", labels={"age_group": "", "revenue": "Revenue"})
                    .update_layout(height=300), width='stretch')
with col4:
    st.subheader("Top Kota Pelanggan")
    city = run_query("""
        SELECT c.city, SUM(f.net_revenue) AS revenue
        FROM fact_sales f JOIN dim_customer c ON f.customer_key = c.customer_key
        GROUP BY c.city ORDER BY revenue DESC LIMIT 10
    """)
    st.plotly_chart(px.bar(city, x="revenue", y="city", orientation="h", color="revenue",
                           color_continuous_scale="Greens", labels={"city": "", "revenue": "Revenue"})
                    .update_layout(height=300, yaxis={"categoryorder": "total ascending"}),
                    width='stretch')

# --- Top customers ---
st.subheader("🏅 Top 15 Pelanggan (repeat & belanja terbanyak)")
top = run_query("""
    SELECT c.full_name, c.city, c.member_tier,
           COUNT(DISTINCT f.transaction_id) AS n_trx,
           SUM(f.net_revenue) AS total
    FROM fact_sales f JOIN dim_customer c ON f.customer_key = c.customer_key
    GROUP BY c.full_name, c.city, c.member_tier
    ORDER BY n_trx DESC, total DESC LIMIT 15
""")
top_disp = top.copy()
top_disp["total"] = top_disp["total"].apply(rupiah)
st.dataframe(top_disp.rename(columns={"full_name": "Nama", "city": "Kota",
             "member_tier": "Tier", "n_trx": "Transaksi", "total": "Total Belanja"}),
             width='stretch', hide_index=True)

st.success(f"💡 **Insight:** Repeat rate **{rate:.1f}%** — segmen *Champion* & *Loyal* "
           f"menjadi tulang punggung revenue. Rancang program loyalti (poin/tier upgrade) "
           f"untuk mengubah pelanggan *Occasional* menjadi repeat buyer.")

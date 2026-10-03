"""Executive Overview: gambaran besar penjualan untuk pemilik toko."""
import sys
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.db import get_filters, run_query  # noqa: E402
from utils import theme as t  # noqa: E402

f = get_filters()
where = f["where"]
JOIN = """FROM fact_sales f
    JOIN dim_store s ON f.store_key = s.store_key
    JOIN dim_date d ON f.date_key = d.date_key"""

t.page_header(
    "Executive Overview",
    "Ringkasan penjualan, profit, dan sumber revenue Rumah Mode Nusantara.",
    t.filter_meta(f))

kpi = run_query(f"""
    SELECT SUM(f.net_revenue) AS revenue,
           SUM(f.gross_profit) AS profit,
           COUNT(DISTINCT f.transaction_id) AS n_trx,
           SUM(CASE WHEN f.channel <> 'offline' THEN f.net_revenue ELSE 0 END) AS online
    {JOIN} {where}
""").iloc[0]
if not kpi["revenue"]:
    t.empty_state()

revenue, profit, n_trx = float(kpi["revenue"]), float(kpi["profit"]), int(kpi["n_trx"])
margin = profit / revenue * 100
aov = revenue / n_trx
online_share = float(kpi["online"]) / revenue * 100

rr = run_query(f"""
    WITH per_cust AS (
        SELECT f.customer_key, COUNT(DISTINCT f.transaction_id) AS n
        {JOIN} {where} {'AND' if where else 'WHERE'} f.customer_key IS NOT NULL
        GROUP BY f.customer_key
    )
    SELECT COUNT(*) AS members,
           100.0 * SUM(CASE WHEN n > 1 THEN 1 ELSE 0 END) / COUNT(*) AS rate
    FROM per_cust
""").iloc[0]

t.kpi_cards([
    ("Revenue", t.rp(revenue), f"{t.num(n_trx)} transaksi"),
    ("Gross profit", t.rp(profit), f"margin {t.pct(margin)}"),
    ("Rata-rata transaksi", t.rp(aov), "nilai per struk"),
    ("Repeat rate", t.pct(rr["rate"] or 0), f"dari {t.num(rr['members'] or 0)} member"),
    ("Porsi online", t.pct(online_share), "dari 3 channel online"),
])

# --- Tren bulanan -----------------------------------------------------------
trend = run_query(f"""
    SELECT d.year, d.month, SUM(f.net_revenue) AS revenue, SUM(f.gross_profit) AS profit
    {JOIN} {where}
    GROUP BY d.year, d.month ORDER BY d.year, d.month
""")
trend["label"] = [f"{t.BULAN[m-1]} {str(y)[2:]}" for y, m in zip(trend["year"], trend["month"])]

t.section("Revenue dan gross profit per bulan",
          "Bulan dengan event belanja besar diberi label di atas titiknya.")
fig = go.Figure()
for col, name, color in [("revenue", "Revenue", t.SERIES[0]), ("profit", "Gross profit", t.SERIES[2])]:
    fig.add_trace(go.Scatter(
        x=trend["label"], y=trend[col] / 1e6, name=name, mode="lines+markers",
        line=dict(color=color), marker=dict(size=8, color=color, line=dict(width=2, color=t.BG)),
        hovertemplate="%{x}<br>" + name + ": Rp %{y:,.1f} jt<extra></extra>"))
EVENTS = {3: "Ramadan", 4: "Lebaran", 11: "Harbolnas 11.11", 12: "Harbolnas 12.12"}
for _, r in trend.nlargest(3, "revenue").iterrows():
    if r["month"] in EVENTS:
        fig.add_annotation(x=r["label"], y=r["revenue"] / 1e6, text=EVENTS[r["month"]],
                           showarrow=False, yshift=18, font=dict(color=t.TEXT_2, size=11))
fig.update_yaxes(title_text="Rp juta", rangemode="tozero")
fig.update_xaxes(gridcolor="rgba(0,0,0,0)")
t.chart(t.style(fig, height=340))
t.source("Revenue bersih setelah diskon. Gross profit = revenue dikurangi harga pokok.")

# --- Kategori dan channel ---------------------------------------------------
c1, c2 = st.columns(2, gap="large")
with c1:
    cat = run_query(f"""
        SELECT p.parent_category AS k, SUM(f.net_revenue) AS revenue,
               100.0 * SUM(f.gross_profit) / SUM(f.net_revenue) AS margin
        {JOIN} JOIN dim_product p ON f.product_key = p.product_key {where}
        GROUP BY p.parent_category ORDER BY revenue DESC
    """)
    share = cat["revenue"] / cat["revenue"].sum() * 100
    t.section("Revenue per kategori", "Label menunjukkan porsi terhadap total revenue.")
    t.chart(t.bar_h(cat["k"], cat["revenue"] / 1e6,
                    text=[t.pct(s) for s in share],
                    hover=[f"{k}<br>{t.rp(v)} ({t.pct(s)})<br>Margin {t.pct(m)}"
                           for k, v, s, m in zip(cat["k"], cat["revenue"], share, cat["margin"])]))
with c2:
    ch = run_query(f"""
        SELECT f.channel AS k, SUM(f.net_revenue) AS revenue,
               COUNT(DISTINCT f.transaction_id) AS n
        {JOIN} {where}
        GROUP BY f.channel ORDER BY revenue DESC
    """)
    chs = ch["revenue"] / ch["revenue"].sum() * 100
    t.section("Revenue per channel", "Label menunjukkan porsi terhadap total revenue.")
    t.chart(t.bar_h(ch["k"].str.capitalize(), ch["revenue"] / 1e6,
                    text=[t.pct(s) for s in chs],
                    hover=[f"{k.capitalize()}<br>{t.rp(v)} ({t.pct(s)})<br>{t.num(n)} transaksi"
                           for k, v, s, n in zip(ch["k"], ch["revenue"], chs, ch["n"])]))

# --- Cabang dan produk ------------------------------------------------------
c3, c4 = st.columns(2, gap="large")
with c3:
    br = run_query(f"""
        SELECT s.store_name AS k, SUM(f.net_revenue) AS revenue
        {JOIN} {where}
        GROUP BY s.store_name ORDER BY revenue DESC
    """)
    t.section("Revenue per cabang", "Jakarta Pusat adalah toko flagship, cabang lain bertipe reguler.")
    t.chart(t.bar_h(br["k"].str.replace("RMN ", ""), br["revenue"] / 1e6,
                    text=[t.rp(v) for v in br["revenue"]],
                    hover=[f"{k}<br>{t.rp_full(v)}" for k, v in zip(br["k"], br["revenue"])],
                    label_room=0.38))
with c4:
    top = run_query(f"""
        SELECT p.product_name AS k, SUM(f.net_revenue) AS revenue, SUM(f.quantity) AS qty
        {JOIN} JOIN dim_product p ON f.product_key = p.product_key {where}
        GROUP BY p.product_name ORDER BY revenue DESC LIMIT 6
    """)
    t.section("Enam produk dengan revenue terbesar")
    t.chart(t.bar_h(top["k"], top["revenue"] / 1e6,
                    text=[t.rp(v) for v in top["revenue"]],
                    hover=[f"{k}<br>{t.rp_full(v)}<br>{t.num(q)} unit"
                           for k, v, q in zip(top["k"], top["revenue"], top["qty"])],
                    label_room=0.38))

# --- Catatan ----------------------------------------------------------------
peak = trend.loc[trend["revenue"].idxmax()]
others = trend.loc[trend.index != trend["revenue"].idxmax(), "revenue"].mean()
points = [
    f"Bulan terbaik adalah <b>{t.BULAN[int(peak['month'])-1]} {int(peak['year'])}</b> "
    f"({t.rp(peak['revenue'])})" + (f", sekitar <b>{peak['revenue']/others:.1f}x</b> rata-rata bulan lain.".replace(".", ",", 1)
                                    if len(trend) > 1 and others else "."),
    f"Kategori <b>{cat.iloc[0]['k']}</b> menyumbang <b>{t.pct(share.iloc[0])}</b> revenue "
    f"dengan margin {t.pct(cat.iloc[0]['margin'])}.",
    f"Channel online menyumbang <b>{t.pct(online_share)}</b> revenue.",
]
if len(br) > 1:
    points.append(f"<b>{br.iloc[0]['k']}</b> memimpin dengan {t.rp(br.iloc[0]['revenue'])}, "
                  f"sedangkan <b>{br.iloc[-1]['k']}</b> paling rendah di {t.rp(br.iloc[-1]['revenue'])}.")
t.note(points)

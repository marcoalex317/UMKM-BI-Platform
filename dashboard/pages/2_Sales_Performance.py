"""Sales Performance: tren harian, channel, metode bayar, dan pola mingguan."""
import sys
from pathlib import Path

import pandas as pd
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
    "Sales Performance",
    "Bagaimana penjualan bergerak dari hari ke hari, lewat channel apa, dan dibayar dengan apa.",
    t.filter_meta(f))

k = run_query(f"""
    SELECT SUM(f.net_revenue) AS revenue, SUM(f.quantity) AS qty,
           COUNT(DISTINCT f.transaction_id) AS n_trx,
           SUM(f.discount) AS disc, SUM(f.gross_revenue) AS gross
    {JOIN} {where}
""").iloc[0]
if not k["revenue"]:
    t.empty_state()

revenue, qty, n_trx = float(k["revenue"]), int(k["qty"]), int(k["n_trx"])
t.kpi_cards([
    ("Revenue", t.rp(revenue), "setelah diskon"),
    ("Unit terjual", t.num(qty), f"{qty / n_trx:.1f} unit per transaksi".replace(".", ",")),
    ("Transaksi", t.num(n_trx), "jumlah struk"),
    ("Rata-rata transaksi", t.rp(revenue / n_trx), "nilai per struk"),
    ("Diskon diberikan", t.rp(k["disc"]), f"{t.pct(k['disc'] / k['gross'] * 100)} dari harga normal"),
])

# --- Tren harian ------------------------------------------------------------
daily = run_query(f"""
    SELECT d.full_date AS tgl, SUM(f.net_revenue) AS revenue
    {JOIN} {where}
    GROUP BY d.full_date ORDER BY d.full_date
""")
daily["tgl"] = pd.to_datetime(daily["tgl"])
daily["ma7"] = daily["revenue"].rolling(7, min_periods=1).mean()

t.section("Revenue harian",
          "Garis tipis adalah angka per hari, garis tebal rata-rata 7 hari supaya trennya terbaca.")
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=daily["tgl"], y=daily["revenue"] / 1e6, name="Per hari", mode="lines",
    line=dict(color=t.DIM, width=1),
    hovertemplate="%{x|%d %b %Y}<br>Rp %{y:,.1f} jt<extra></extra>"))
fig.add_trace(go.Scatter(
    x=daily["tgl"], y=daily["ma7"] / 1e6, name="Rata-rata 7 hari", mode="lines",
    line=dict(color=t.ACCENT, width=2.5),
    hovertemplate="%{x|%d %b %Y}<br>Rata-rata 7 hari: Rp %{y:,.1f} jt<extra></extra>"))
fig.update_yaxes(title_text="Rp juta", rangemode="tozero")
months = pd.date_range(daily["tgl"].min().replace(day=1), daily["tgl"].max(), freq="MS")
fig.update_xaxes(gridcolor="rgba(0,0,0,0)", tickvals=months,
                 ticktext=[f"{t.BULAN[m.month-1]} {str(m.year)[2:]}" for m in months])
fig.update_layout(hovermode="x unified")
t.chart(t.style(fig, height=320))
top_day = daily.loc[daily["revenue"].idxmax()]
t.source(f"Hari dengan revenue tertinggi: {t.tgl(top_day['tgl'])} ({t.rp(top_day['revenue'])}).")

# --- Channel ----------------------------------------------------------------
t.section("Revenue bulanan per channel",
          "Warna channel sama di semua halaman.")
chm = run_query(f"""
    SELECT d.year, d.month, f.channel, SUM(f.net_revenue) AS revenue
    {JOIN} {where}
    GROUP BY d.year, d.month, f.channel ORDER BY d.year, d.month
""")
chm["label"] = [f"{t.BULAN[m-1]} {str(y)[2:]}" for y, m in zip(chm["year"], chm["month"])]
fig = go.Figure()
for chn in ["offline", "shopee", "tokopedia", "instagram"]:
    sub = chm[chm["channel"] == chn]
    if sub.empty:
        continue
    color = t.CHANNEL_COLORS[chn]
    fig.add_trace(go.Scatter(
        x=sub["label"], y=sub["revenue"] / 1e6, name=chn.capitalize(), mode="lines+markers",
        line=dict(color=color), marker=dict(size=7, color=color, line=dict(width=2, color=t.BG)),
        hovertemplate=chn.capitalize() + "<br>%{x}: Rp %{y:,.1f} jt<extra></extra>"))
fig.update_yaxes(title_text="Rp juta", rangemode="tozero")
fig.update_xaxes(gridcolor="rgba(0,0,0,0)")
t.chart(t.style(fig, height=320))

c1, c2 = st.columns([1.6, 1], gap="large")
with c1:
    ch = run_query(f"""
        SELECT f.channel, SUM(f.net_revenue) AS revenue,
               COUNT(DISTINCT f.transaction_id) AS n_trx,
               SUM(f.gross_profit) AS profit
        {JOIN} {where}
        GROUP BY f.channel ORDER BY revenue DESC
    """)
    tbl = pd.DataFrame({
        "Channel": ch["channel"].str.capitalize(),
        "Revenue": [t.rp(v) for v in ch["revenue"]],
        "Porsi": [t.pct(v) for v in ch["revenue"] / ch["revenue"].sum() * 100],
        "": ch["revenue"] / ch["revenue"].sum() * 100,
        "Transaksi": [t.num(v) for v in ch["n_trx"]],
        "Rata-rata transaksi": [t.rp(r / n) for r, n in zip(ch["revenue"], ch["n_trx"])],
        "Margin": [t.pct(p / r * 100) for p, r in zip(ch["profit"], ch["revenue"])],
    })
    t.section("Ringkasan per channel")
    st.dataframe(tbl, hide_index=True, width="stretch", column_config={
        "": st.column_config.ProgressColumn(" ", format=" ", min_value=0, max_value=100, width="small"),
    })
with c2:
    pay = run_query(f"""
        SELECT st.payment_method AS k, SUM(f.net_revenue) AS revenue,
               COUNT(DISTINCT f.transaction_id) AS n
        {JOIN} JOIN sales_transactions st ON f.transaction_id = st.transaction_id {where}
        GROUP BY st.payment_method ORDER BY revenue DESC
    """)
    ps = pay["revenue"] / pay["revenue"].sum() * 100
    t.section("Metode pembayaran", "Porsi revenue per metode.")
    t.chart(t.bar_h(pay["k"], pay["revenue"] / 1e6, text=[t.pct(v) for v in ps],
                    hover=[f"{k}<br>{t.rp(v)}<br>{t.num(n)} transaksi"
                           for k, v, n in zip(pay["k"], pay["revenue"], pay["n"])],
                    height=300, label_room=0.22))

# --- Pola mingguan ----------------------------------------------------------
dow = run_query(f"""
    SELECT d.day_of_week AS dw, d.day_name AS hari,
           SUM(f.net_revenue) * 1.0 / COUNT(DISTINCT d.full_date) AS avg_rev
    {JOIN} {where}
    GROUP BY d.day_of_week, d.day_name ORDER BY d.day_of_week
""")
weekend = dow["dw"] >= 5
t.section("Rata-rata revenue per hari dalam seminggu",
          "Dihitung per tanggal supaya jumlah Senin dan Minggu yang berbeda tidak memengaruhi. "
          "Sabtu dan Minggu diberi warna terang.")
t.chart(t.bar_v(dow["hari"], dow["avg_rev"] / 1e6,
                text=[t.rp(v) for v in dow["avg_rev"]],
                hover=[f"{h}<br>Rata-rata {t.rp_full(v)} per hari" for h, v in zip(dow["hari"], dow["avg_rev"])],
                colors=[t.ACCENT if w else t.DIM for w in weekend], height=290))

wk = dow.loc[weekend, "avg_rev"].mean()
wd = dow.loc[~weekend, "avg_rev"].mean()
online_rev = ch.loc[ch["channel"] != "offline", "revenue"].sum()
points = [
    f"Rata-rata revenue akhir pekan <b>{t.rp(wk)}</b> per hari, "
    f"{'lebih tinggi' if wk > wd else 'lebih rendah'} <b>{t.pct(abs(wk / wd - 1) * 100)}</b> dibanding hari kerja ({t.rp(wd)}).",
    f"<b>{ch.iloc[0]['channel'].capitalize()}</b> adalah channel terbesar dengan "
    f"{t.pct(ch.iloc[0]['revenue'] / revenue * 100)} revenue. Gabungan tiga channel online "
    f"{t.pct(online_rev / revenue * 100)}.",
    f"Metode pembayaran tersebar rata. Yang terbesar, <b>{pay.iloc[0]['k']}</b>, hanya "
    f"{t.pct(ps.iloc[0])}, jadi tidak ada satu metode yang wajib diprioritaskan.",
]
t.note(points)

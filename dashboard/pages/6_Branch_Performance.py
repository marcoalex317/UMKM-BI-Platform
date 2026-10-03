"""Kinerja Cabang: ranking, komposisi channel, dan tren bulanan per cabang."""
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
    "Kinerja Cabang",
    "Perbandingan enam cabang. Biaya operasional tidak tersedia, jadi penilaian berhenti di gross profit.",
    t.filter_meta(f))

rank = run_query(f"""
    SELECT s.store_name, s.city, s.store_type,
           COUNT(DISTINCT f.transaction_id) AS n_trx,
           SUM(f.net_revenue) AS revenue, SUM(f.gross_profit) AS profit
    {JOIN} {where}
    GROUP BY s.store_name, s.city, s.store_type
    ORDER BY revenue DESC
""")
if rank.empty:
    t.empty_state()

rank["short"] = rank["store_name"].str.replace("RMN ", "", regex=False)
best, worst = rank.iloc[0], rank.iloc[-1]
reg = rank[rank["store_type"] == "regular"]

t.kpi_cards([
    ("Cabang terbaik", best["city"], t.rp(best["revenue"])),
    ("Cabang terlemah", worst["city"], t.rp(worst["revenue"])),
    ("Selisih", f"{best['revenue'] / worst['revenue']:.1f}x".replace(".", ","), "terbaik dibanding terlemah"),
    ("Rata-rata reguler", t.rp(reg["revenue"].mean()) if len(reg) else "-",
     f"{len(reg)} cabang non-flagship"),
    ("Margin tertinggi", t.pct((rank["profit"] / rank["revenue"]).max() * 100),
     rank.loc[(rank["profit"] / rank["revenue"]).idxmax(), "city"]),
])

# --- Ranking ----------------------------------------------------------------
t.section("Ranking cabang", "Diurutkan dari revenue terbesar.")
st.dataframe(pd.DataFrame({
    "Cabang": rank["store_name"],
    "Tipe": rank["store_type"].str.capitalize(),
    "Revenue": [t.rp(v) for v in rank["revenue"]],
    "Porsi": [t.pct(v) for v in rank["revenue"] / rank["revenue"].sum() * 100],
    "": rank["revenue"] / rank["revenue"].sum() * 100,
    "Gross profit": [t.rp(v) for v in rank["profit"]],
    "Margin": [t.pct(v) for v in rank["profit"] / rank["revenue"] * 100],
    "Transaksi": [t.num(v) for v in rank["n_trx"]],
    "Rata-rata transaksi": [t.rp(r / n) for r, n in zip(rank["revenue"], rank["n_trx"])],
}), hide_index=True, width="stretch", column_config={
    "": st.column_config.ProgressColumn(" ", format=" ", min_value=0, width="small",
                                        max_value=float((rank["revenue"] / rank["revenue"].sum() * 100).max())),
})

c1, c2 = st.columns([1, 1.15], gap="large")

# --- Komposisi channel ------------------------------------------------------
with c1:
    mix = run_query(f"""
        SELECT s.store_name, f.channel, SUM(f.net_revenue) AS revenue
        {JOIN} {where}
        GROUP BY s.store_name, f.channel
    """)
    piv = mix.pivot(index="store_name", columns="channel", values="revenue").fillna(0)
    share = piv.div(piv.sum(axis=1), axis=0) * 100
    share = share.reindex(rank["store_name"][::-1])
    share.index = share.index.str.replace("RMN ", "", regex=False)
    t.section("Komposisi channel per cabang", "Porsi revenue tiap cabang, totalnya 100%.")
    fig = go.Figure()
    for chn in ["offline", "shopee", "tokopedia", "instagram"]:
        if chn not in share:
            continue
        fig.add_trace(go.Bar(
            y=share.index, x=share[chn], name=chn.capitalize(), orientation="h",
            marker_color=t.CHANNEL_COLORS[chn], marker_line=dict(width=2, color=t.BG),
            hovertemplate="%{y}<br>" + chn.capitalize() + ": %{x:.1f}%<extra></extra>"))
    fig.update_layout(barmode="stack", legend_traceorder="normal")
    fig.update_xaxes(title_text="% revenue", range=[0, 100], ticksuffix="%")
    fig.update_yaxes(gridcolor="rgba(0,0,0,0)", tickfont=dict(color=t.TEXT_2, size=12))
    t.chart(t.style(fig, height=340))

# --- Tren per cabang --------------------------------------------------------
with c2:
    trend = run_query(f"""
        SELECT s.store_name, d.year, d.month, SUM(f.net_revenue) AS revenue
        {JOIN} {where}
        GROUP BY s.store_name, d.year, d.month ORDER BY d.year, d.month
    """)
    trend["label"] = [f"{t.BULAN[m-1]} {str(y)[2:]}" for y, m in zip(trend["year"], trend["month"])]
    t.section("Tren bulanan per cabang", "Pilih satu cabang untuk disorot, cabang lain tampil samar.")
    names = list(rank["store_name"])
    pick = st.selectbox("Sorot cabang", names, index=len(names) - 1,
                        format_func=lambda s: s.replace("RMN ", ""), label_visibility="collapsed")
    fig = go.Figure()
    for name in names:
        sub = trend[trend["store_name"] == name]
        on = name == pick
        fig.add_trace(go.Scatter(
            x=sub["label"], y=sub["revenue"] / 1e6, mode="lines" + ("+markers" if on else ""),
            name=name.replace("RMN ", ""), showlegend=False,
            line=dict(color=t.ACCENT if on else t.DIM, width=2.5 if on else 1.2),
            marker=dict(size=7, color=t.ACCENT, line=dict(width=2, color=t.BG)),
            hovertemplate=name.replace("RMN ", "") + "<br>%{x}: Rp %{y:,.1f} jt<extra></extra>"))
        if on and len(sub):
            last = sub.iloc[-1]
            fig.add_annotation(x=last["label"], y=last["revenue"] / 1e6, text=name.replace("RMN ", "").split()[0],
                               showarrow=False, xanchor="left", xshift=8,
                               font=dict(color=t.TEXT, size=12))
    # garis sorotan digambar paling akhir supaya berada di atas
    fig.data = tuple(sorted(fig.data, key=lambda tr: tr.line.color == t.ACCENT))
    fig.update_yaxes(title_text="Rp juta", rangemode="tozero")
    fig.update_xaxes(gridcolor="rgba(0,0,0,0)", tickangle=0, dtick=2)
    fig.update_layout(margin=dict(r=70))
    t.chart(t.style(fig, height=300))

# --- Catatan ----------------------------------------------------------------
points = [
    f"<b>{best['store_name']}</b> ({best['store_type']}) memimpin dengan {t.rp(best['revenue'])}, "
    f"{t.pct(best['revenue'] / rank['revenue'].sum() * 100)} dari total.",
]
if len(reg) > 1:
    weakest_reg = reg.iloc[-1]
    second = reg.iloc[-2]
    points.append(
        f"<b>{weakest_reg['store_name']}</b> hanya {t.rp(weakest_reg['revenue'])}, sekitar "
        f"{t.pct(weakest_reg['revenue'] / second['revenue'] * 100, 0)} dari cabang reguler terlemah berikutnya "
        f"({second['short']}).")
m = rank["profit"] / rank["revenue"] * 100
if m.max() - m.min() < 2:
    points.append(f"Margin antar cabang hampir sama ({t.pct(m.min())} sampai {t.pct(m.max())}), "
                  "jadi selisih profit terutama datang dari volume penjualan.")
else:
    points.append(f"Margin antar cabang berkisar {t.pct(m.min())} sampai {t.pct(m.max())}.")
points.append("Sebelum memutuskan nasib cabang terlemah, data sewa, gaji, dan biaya lain perlu dikumpulkan dulu.")
t.note(points)

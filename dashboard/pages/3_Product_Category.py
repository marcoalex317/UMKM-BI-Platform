"""Produk & Kategori: produk laris, margin riil, Pareto kategori, ukuran dan warna."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.db import get_filters, run_query  # noqa: E402
from utils import theme as t  # noqa: E402

f = get_filters()
where = f["where"]
JOIN = """FROM fact_sales f
    JOIN dim_product p ON f.product_key = p.product_key
    JOIN dim_store s ON f.store_key = s.store_key
    JOIN dim_date d ON f.date_key = d.date_key"""
THIN = 25  # batas margin harga jual (%) untuk menandai produk bermargin tipis

t.page_header(
    "Produk & Kategori",
    "Produk mana yang mendatangkan uang, mana yang laris tapi hampir tidak menghasilkan untung.",
    t.filter_meta(f))

sku = run_query(f"""
    SELECT p.product_key, p.product_name, p.size, p.category, p.margin_pct AS list_margin,
           SUM(f.quantity) AS qty, SUM(f.net_revenue) AS revenue,
           SUM(f.gross_profit) AS profit
    {JOIN} {where}
    GROUP BY p.product_key, p.product_name, p.size, p.category, p.margin_pct
    ORDER BY revenue DESC
""")
if sku.empty:
    t.empty_state()

sku["margin"] = sku["profit"] / sku["revenue"] * 100
sku["label"] = sku["product_name"] + " (" + sku["size"] + ")"
# Satu nama produk bisa punya beberapa SKU (ukuran berbeda). Untuk ranking produk
# semua ukuran digabung, sama seperti di Executive Overview.
prod = (sku.groupby(["product_name", "category"], as_index=False)[["qty", "revenue", "profit"]].sum()
           .sort_values("revenue", ascending=False))
prod["margin"] = prod["profit"] / prod["revenue"] * 100
tot_rev, tot_gp = sku["revenue"].sum(), sku["profit"].sum()
thin = sku[sku["list_margin"] < THIN]
top10_share = prod["revenue"].head(10).sum() / tot_rev * 100

t.kpi_cards([
    ("SKU terjual", t.num(len(sku)), f"dari {t.num(sku['category'].nunique())} kategori"),
    ("Porsi 10 produk teratas", t.pct(top10_share), "dari total revenue"),
    ("Produk nomor satu", t.pct(prod.iloc[0]["revenue"] / tot_rev * 100), "porsi revenue satu produk"),
    ("Margin riil rata-rata", t.pct(tot_gp / tot_rev * 100), "setelah diskon"),
    ("SKU margin tipis", t.num(len(thin)), f"margin jual di bawah {THIN}%"),
])

# --- Revenue vs margin ------------------------------------------------------
t.section("Revenue dan margin riil per SKU",
          f"Setiap titik satu SKU. Titik oranye adalah SKU dengan margin harga jual di bawah {THIN}%. "
          "Garis putus-putus menunjukkan margin riil rata-rata.")
avg_m = tot_gp / tot_rev * 100
fig = go.Figure()
for mask, name, color, size in [(sku["list_margin"] >= THIN, "SKU lain", t.ACCENT, 9),
                                (sku["list_margin"] < THIN, f"Margin tipis (< {THIN}%)", t.SERIES[1], 10)]:
    sub = sku[mask]
    fig.add_trace(go.Scatter(
        x=sub["revenue"] / 1e6, y=sub["margin"], mode="markers", name=name,
        marker=dict(size=size, color=color, opacity=0.85, line=dict(width=1.5, color=t.BG)),
        text=sub["label"],
        customdata=np.stack([sub["category"], sub["qty"], sub["list_margin"]], axis=-1),
        hovertemplate="<b>%{text}</b><br>%{customdata[0]}<br>Revenue Rp %{x:,.1f} jt"
                      "<br>Margin riil %{y:.1f}%<br>Margin harga jual %{customdata[2]:.1f}%"
                      "<br>%{customdata[1]:,} unit<extra></extra>"))
fig.add_hline(y=avg_m, line=dict(color=t.MUTED, width=1, dash="dot"))
fig.add_annotation(x=0.5, xref="paper", y=avg_m, text=f"rata-rata {t.pct(avg_m)}",
                   showarrow=False, xanchor="center", yshift=10, font=dict(color=t.MUTED, size=11))
fig.update_xaxes(title_text="Revenue (Rp juta)", rangemode="tozero")
fig.update_yaxes(title_text="Margin riil (%)", rangemode="tozero")
t.chart(t.style(fig, height=380))
t.source("Margin riil = gross profit dibagi revenue setelah diskon. "
         "Margin harga jual = selisih harga jual dan harga pokok sebelum diskon.")

# --- Pareto kategori dan tabel produk ---------------------------------------
c1, c2 = st.columns([0.9, 1.3], gap="large")
with c1:
    cat = (sku.groupby("category", as_index=False)[["revenue", "profit"]].sum()
              .sort_values("revenue", ascending=False).head(12))
    all_cat = sku.groupby("category")["revenue"].sum().sort_values(ascending=False)
    cum = (all_cat.cumsum() / all_cat.sum() * 100).loc[cat["category"]]
    n80 = int((all_cat.cumsum() / all_cat.sum() * 100 < 80).sum()) + 1
    t.section("Kategori dan porsi kumulatif",
              f"Label menunjukkan porsi kumulatif. {n80} dari {len(all_cat)} kategori "
              "sudah mencapai 80% revenue.")
    t.chart(t.bar_h(cat["category"], cat["revenue"] / 1e6,
                    text=[t.pct(c, 0) for c in cum],
                    hover=[f"{k}<br>{t.rp(v)}<br>Kumulatif {t.pct(c)}"
                           for k, v, c in zip(cat["category"], cat["revenue"], cum)],
                    colors=[t.ACCENT if c <= 80 or i == 0 else t.DIM
                            for i, c in enumerate(cum)],
                    label_room=0.2))
with c2:
    top = prod.head(10)
    tbl = pd.DataFrame({
        "Produk": top["product_name"],
        "Kategori": top["category"],
        "Unit": [t.num(v) for v in top["qty"]],
        "Revenue": [t.rp(v) for v in top["revenue"]],
        "Margin riil": [t.pct(v) for v in top["margin"]],
    })
    t.section("Sepuluh produk dengan revenue terbesar", "Semua ukuran dari produk yang sama digabung.")
    st.dataframe(tbl, hide_index=True, width="stretch", height=388)

# --- Ukuran dan warna -------------------------------------------------------
attr = run_query(f"""
    SELECT p.size, p.color, SUM(f.quantity) AS qty
    {JOIN} {where}
    GROUP BY p.size, p.color
""")
c3, c4 = st.columns(2, gap="large")
with c3:
    order = ["S", "M", "L", "XL", "All Size"]
    sz = attr.groupby("size")["qty"].sum().reindex(order).dropna()
    t.section("Unit terjual per ukuran", "All Size untuk aksesori seperti topi dan tas.")
    t.chart(t.bar_v(sz.index, sz.values, text=[t.num(v) for v in sz.values],
                    hover=[f"Ukuran {k}<br>{t.num(v)} unit" for k, v in sz.items()],
                    ytitle="Unit", height=290))
with c4:
    cl = attr.groupby("color")["qty"].sum().sort_values(ascending=False)
    t.section("Unit terjual per warna")
    t.chart(t.bar_h(cl.index, cl.values, text=[t.num(v) for v in cl.values],
                    hover=[f"{k}<br>{t.num(v)} unit" for k, v in cl.items()],
                    xtitle="Unit", height=290, label_room=0.2))

# --- Catatan ----------------------------------------------------------------
worst = thin.sort_values("revenue", ascending=False).head(1)
lead = prod.iloc[0]
points = [
    f"<b>{lead['product_name']}</b> sendirian menyumbang <b>{t.pct(lead['revenue'] / tot_rev * 100)}</b> "
    f"revenue ({t.rp(lead['revenue'])}). Pasokannya perlu diamankan.",
]
if len(thin):
    points.append(
        f"{len(thin)} SKU bermargin tipis menyerap <b>{t.pct(thin['revenue'].sum() / tot_rev * 100)}</b> "
        f"revenue tapi hanya <b>{t.pct(thin['profit'].sum() / tot_gp * 100)}</b> gross profit.")
if len(worst):
    w = worst.iloc[0]
    points.append(f"Contoh paling jelas: <b>{w['label']}</b>, revenue {t.rp(w['revenue'])} "
                  f"dengan margin riil hanya {t.pct(w['margin'])}.")
points.append(f"Ukuran <b>{sz.idxmax()}</b> dan warna <b>{cl.index[0]}</b> paling banyak terjual. "
              "Ini bisa jadi patokan komposisi stok saat restock.")
t.note(points)

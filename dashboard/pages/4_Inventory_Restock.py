"""Inventori & Restock: posisi stok, prioritas restock, dan dead stock."""
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.db import run_query  # noqa: E402
from utils import theme as t  # noqa: E402

DEAD_MAX = 5  # terjual 5 unit atau kurang setahun dianggap dead stock

# Stok terkini = baris terakhir per produk per toko, lalu dijumlah per produk.
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
    SELECT product_key, SUM(quantity) AS qty_sold, SUM(quantity) / 12.0 AS avg_month
    FROM fact_sales GROUP BY product_key
)
"""

asof = run_query("SELECT MAX(d.full_date) AS d FROM fact_inventory i "
                 "JOIN dim_date d ON i.date_key = d.date_key").iloc[0]["d"]
t.page_header(
    "Inventori & Restock",
    "Posisi stok di semua cabang: apa yang harus segera dipesan, dan modal yang tertahan di barang tidak laku.",
    f"Posisi stok per <b>{t.tgl(asof)}</b> &nbsp;·&nbsp; seluruh cabang &nbsp;·&nbsp; nilai stok dihitung dengan harga pokok")

prod = run_query(STOCK_CTE + """
    SELECT p.product_name, p.category, p.parent_category, p.brand, p.cost_price,
           COALESCE(s.stock_now, 0) AS stok,
           COALESCE(so.qty_sold, 0) AS terjual,
           COALESCE(so.avg_month, 0) AS per_bulan
    FROM dim_product p
    LEFT JOIN stock s ON p.product_key = s.product_key
    LEFT JOIN sold so ON p.product_key = so.product_key
""")
prod["nilai"] = prod["stok"] * prod["cost_price"]
prod["dead"] = prod["terjual"] <= DEAD_MAX
prod["cover"] = prod["stok"] / prod["per_bulan"].where(prod["per_bulan"] > 0)

active = prod[prod["per_bulan"] > 2].copy()
urgent = active[active["cover"] < 1]
soon = active[(active["cover"] >= 1) & (active["cover"] < 2)]
dead = prod[prod["dead"]]
total_val = prod["nilai"].sum()

t.kpi_cards([
    ("Nilai stok", t.rp(total_val), f"{t.num(prod['stok'].sum())} unit"),
    ("Restock urgent", t.num(len(urgent)), "stok kurang dari 1 bulan"),
    ("Restock segera", t.num(len(soon)), "stok 1 sampai 2 bulan"),
    ("Dead stock", f"{t.num(len(dead))} SKU", f"terjual maks. {DEAD_MAX} unit setahun"),
    ("Modal tertahan", t.rp(dead["nilai"].sum()), f"{t.pct(dead['nilai'].sum() / total_val * 100)} dari nilai stok"),
])

# --- Prioritas restock ------------------------------------------------------
t.section("Prioritas restock",
          "Produk yang terjual lebih dari 2 unit per bulan, diurutkan dari stok yang paling cepat habis. "
          "Rata-rata penjualan dihitung dari 12 bulan terakhir.")


def status(c: float) -> str:
    if c < 1:
        return "Urgent"
    if c < 2:
        return "Segera"
    return "Aman"


rs = active.sort_values("cover").head(15)
tbl = pd.DataFrame({
    "Status": [status(c) for c in rs["cover"]],
    "Produk": rs["product_name"],
    "Kategori": rs["category"],
    "Jual per bulan": rs["per_bulan"].round(1),
    "Stok": rs["stok"].astype(int),
    "Cukup untuk": rs["cover"].round(1),
})
STATUS_COLOR = {"Urgent": t.STATUS["critical"], "Segera": t.STATUS["warning"], "Aman": t.STATUS["good"]}
styled = (tbl.style
          .map(lambda v: f"color: {STATUS_COLOR.get(v, t.TEXT)}; font-weight: 600", subset=["Status"])
          .format({"Jual per bulan": "{:.1f}", "Cukup untuk": "{:.1f} bln"}, decimal=","))
st.dataframe(styled, hide_index=True, width="stretch", height=35 * (len(tbl) + 1) + 3)

# --- Nilai stok dan dead stock ---------------------------------------------
c1, c2 = st.columns([1, 1.3], gap="large")
with c1:
    val = (prod.groupby(["parent_category", "dead"])["nilai"].sum().unstack(fill_value=0)
               .rename(columns={False: "aktif", True: "dead"}))
    for col in ("aktif", "dead"):
        if col not in val:
            val[col] = 0
    val = val.assign(total=val.sum(axis=1)).sort_values("total")
    t.section("Nilai stok per kategori induk",
              "Bagian oranye adalah modal yang tertahan di dead stock.")
    fig = go.Figure()
    for col, name, color in [("aktif", "Stok aktif", t.ACCENT), ("dead", "Dead stock", t.SERIES[1])]:
        fig.add_trace(go.Bar(
            y=val.index, x=val[col] / 1e6, name=name, orientation="h", marker_color=color,
            marker_line=dict(width=2, color=t.BG),
            hovertemplate="%{y}<br>" + name + ": Rp %{x:,.1f} jt<extra></extra>"))
    fig.update_layout(barmode="stack", legend_traceorder="normal")
    fig.update_xaxes(title_text="Rp juta")
    fig.update_yaxes(gridcolor="rgba(0,0,0,0)", tickfont=dict(color=t.TEXT_2, size=12))
    t.chart(t.style(fig, height=330))
with c2:
    ds = dead.sort_values("nilai", ascending=False)
    t.section("Daftar dead stock",
              f"{len(ds)} SKU, diurutkan dari modal tertahan terbesar.")
    st.dataframe(pd.DataFrame({
        "Produk": ds["product_name"],
        "Terjual setahun": ds["terjual"].astype(int),
        "Stok": ds["stok"].astype(int),
        "Modal tertahan": [t.rp(v) for v in ds["nilai"]],
    }), hide_index=True, width="stretch", height=330)

# --- Catatan ----------------------------------------------------------------
top_dead_cat = val["dead"].idxmax() if val["dead"].sum() else "-"
points = [
    f"<b>{t.rp(dead['nilai'].sum())}</b> modal tertahan di {len(dead)} SKU dead stock, atau "
    f"{t.pct(dead['nilai'].sum() / total_val * 100)} dari seluruh nilai stok. Paling besar di kategori "
    f"<b>{top_dead_cat}</b>.",
    "Clearance dengan diskon 30 sampai 50% bisa mengembalikan kas sekitar Rp 349 sampai 488 juta "
    "(perhitungan ada di insight report).",
    f"<b>{len(urgent)} produk</b> diperkirakan habis dalam kurang dari sebulan. Pesanan ulang perlu "
    "dibuat sekarang, terutama menjelang Ramadan dan Harbolnas.",
]
t.note(points)

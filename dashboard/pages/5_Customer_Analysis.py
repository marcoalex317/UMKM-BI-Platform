"""Pelanggan: repeat rate, frekuensi belanja, tier member, segmen, dan usia."""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.db import run_query  # noqa: E402
from utils import theme as t  # noqa: E402

t.page_header(
    "Pelanggan",
    "Seberapa sering member kembali belanja, dan apakah tier member benar-benar membedakan pelanggan.",
    "Seluruh periode &nbsp;·&nbsp; hanya transaksi member, pembeli non-member tidak punya ID pelanggan")

cust = run_query("""
    SELECT c.customer_key, c.customer_id, c.city, c.member_tier, c.age_group,
           COUNT(DISTINCT f.transaction_id) AS n_trx,
           SUM(f.net_revenue) AS spend, SUM(f.gross_profit) AS profit
    FROM fact_sales f JOIN dim_customer c ON f.customer_key = c.customer_key
    GROUP BY c.customer_key, c.customer_id, c.city, c.member_tier, c.age_group
""")
guest = run_query("""
    SELECT SUM(CASE WHEN customer_key IS NULL THEN net_revenue ELSE 0 END) AS g,
           SUM(net_revenue) AS total FROM fact_sales
""").iloc[0]

n = len(cust)
rep = cust["n_trx"] > 1
rate = rep.mean() * 100
t.kpi_cards([
    ("Member aktif", t.num(n), "punya transaksi"),
    ("Repeat rate", t.pct(rate), "belanja lebih dari sekali"),
    ("Belanja per member", t.rp(cust["spend"].mean()), "rata-rata setahun"),
    ("Transaksi per member", f"{cust['n_trx'].mean():.2f}".replace(".", ","), "rata-rata setahun"),
    ("Revenue non-member", t.pct(guest["g"] / guest["total"] * 100), t.rp(guest["g"])),
])

# --- Frekuensi dan nilai repeat --------------------------------------------
c1, c2 = st.columns(2, gap="large")
with c1:
    bins = cust["n_trx"].clip(upper=5).map(lambda v: "5+" if v >= 5 else str(int(v)))
    freq = bins.value_counts().reindex(["1", "2", "3", "4", "5+"], fill_value=0)
    t.section("Jumlah member menurut frekuensi belanja",
              "Batang pertama adalah member yang baru belanja sekali.")
    t.chart(t.bar_v([("5x atau lebih" if k == "5+" else f"{k}x") for k in freq.index], freq.values,
                    text=[f"{t.num(v)} ({t.pct(v / n * 100, 0)})" for v in freq.values],
                    hover=[f"{k} transaksi<br>{t.num(v)} member" for k, v in freq.items()],
                    colors=[t.DIM] + [t.ACCENT] * 4, ytitle="Member", height=300))
with c2:
    grp = cust.assign(tipe=rep.map({True: "Repeat", False: "Sekali belanja"})).groupby("tipe").agg(
        member=("customer_key", "count"), spend=("spend", "mean"), profit=("profit", "mean"))
    grp = grp.reindex(["Sekali belanja", "Repeat"])
    t.section("Belanja rata-rata: sekali belanja vs repeat",
              "Nilai per member dalam setahun.")
    t.chart(t.bar_v(grp.index, grp["spend"] / 1e6,
                    text=[t.rp(v) for v in grp["spend"]],
                    hover=[f"{k}<br>{t.num(m)} member<br>Belanja {t.rp(s)}<br>Gross profit {t.rp(p)}"
                           for k, m, s, p in zip(grp.index, grp["member"], grp["spend"], grp["profit"])],
                    colors=[t.DIM, t.ACCENT], height=300))

# --- Tier member ------------------------------------------------------------
t.section("Perbandingan tier member",
          "Kalau tier bekerja, Gold seharusnya belanja lebih banyak dan lebih sering daripada Bronze.")
tier = cust.groupby("member_tier").agg(
    member=("customer_key", "count"), revenue=("spend", "sum"),
    spend=("spend", "mean"), trx=("n_trx", "mean"),
    repeat=("n_trx", lambda s: (s > 1).mean() * 100)).reindex(["Bronze", "Silver", "Gold"])
c3, c4 = st.columns([0.85, 1.5], gap="large")
with c3:
    t.chart(t.bar_v(tier.index, tier["spend"] / 1e3,
                    text=[t.rp(v) for v in tier["spend"]],
                    hover=[f"{k}<br>Belanja per member {t.rp_full(v)}" for k, v in tier["spend"].items()],
                    ytitle="Belanja per member (Rp ribu)", height=290))
with c4:
    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
    st.dataframe(pd.DataFrame({
        "Tier": tier.index,
        "Member": [t.num(v) for v in tier["member"]],
        "Revenue": [t.rp(v) for v in tier["revenue"]],
        "Belanja per member": [t.rp(v) for v in tier["spend"]],
        "Transaksi per member": [f"{v:.2f}".replace(".", ",") for v in tier["trx"]],
        "Repeat rate": [t.pct(v) for v in tier["repeat"]],
    }), hide_index=True, width="stretch")

# --- Segmen dan usia --------------------------------------------------------
c5, c6 = st.columns(2, gap="large")
with c5:
    def segmen(r) -> str:
        if r.n_trx >= 4 and r.spend >= 1_000_000:
            return "Champion"
        if r.n_trx >= 2:
            return "Loyal"
        if r.spend >= 1_000_000:
            return "Big spender"
        return "Occasional"
    cust["segmen"] = [segmen(r) for r in cust.itertuples()]
    seg = cust.groupby("segmen").agg(member=("customer_key", "count"), revenue=("spend", "sum")) \
              .sort_values("revenue", ascending=False)
    rs = seg["revenue"] / seg["revenue"].sum() * 100
    t.section("Segmen pelanggan", "Porsi revenue member per segmen. Definisi segmen ada di halaman Catatan Data.")
    t.chart(t.bar_h(seg.index, seg["revenue"] / 1e6, text=[t.pct(v) for v in rs],
                    hover=[f"{k}<br>{t.num(m)} member<br>{t.rp(v)}"
                           for k, m, v in zip(seg.index, seg["member"], seg["revenue"])],
                    height=260, label_room=0.2))
with c6:
    age = cust.groupby("age_group").agg(member=("customer_key", "count"), revenue=("spend", "sum"))
    ars = age["revenue"] / age["revenue"].sum() * 100
    t.section("Revenue per kelompok usia", "Porsi revenue member.")
    t.chart(t.bar_v(age.index, age["revenue"] / 1e6, text=[t.pct(v) for v in ars],
                    hover=[f"Usia {k}<br>{t.num(m)} member<br>{t.rp(v)}"
                           for k, m, v in zip(age.index, age["member"], age["revenue"])],
                    height=260))

# --- Member teratas ---------------------------------------------------------
t.section("Sepuluh member dengan belanja terbesar",
          "Nama tidak ditampilkan, cukup ID member.")
top = cust.sort_values("spend", ascending=False).head(10)
st.dataframe(pd.DataFrame({
    "ID member": [f"CUST-{int(i):05d}" for i in top["customer_id"]],
    "Kota": top["city"],
    "Tier": top["member_tier"],
    "Transaksi": top["n_trx"].astype(int),
    "Total belanja": [t.rp(v) for v in top["spend"]],
}), hide_index=True, width="stretch")

# --- Catatan ----------------------------------------------------------------
ratio = grp.loc["Repeat", "spend"] / grp.loc["Sekali belanja", "spend"]
ratio_s = f"{ratio:.1f}".replace(".", ",")
points = [
    f"Repeat rate <b>{t.pct(rate)}</b>. Sebanyak {t.num(freq['1'])} member "
    f"({t.pct(freq['1'] / n * 100)}) baru belanja sekali.",
    f"Member repeat belanja <b>{ratio_s}x</b> lebih banyak daripada yang sekali belanja "
    f"({t.rp(grp.loc['Repeat', 'spend'])} vs {t.rp(grp.loc['Sekali belanja', 'spend'])}).",
    f"Belanja per member hampir sama di semua tier (Bronze {t.rp(tier.loc['Bronze', 'spend'])}, "
    f"Silver {t.rp(tier.loc['Silver', 'spend'])}, Gold {t.rp(tier.loc['Gold', 'spend'])}). "
    "Syarat dan benefit tier perlu ditinjau ulang.",
    "Program untuk mendorong pembelian kedua lebih berdampak daripada menambah benefit tier.",
]
t.note(points)

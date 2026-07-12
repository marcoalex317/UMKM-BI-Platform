"""
generate_data.py
================
Generate synthetic dataset realistis untuk UMKM fashion "Rumah Mode Nusantara".

Karakteristik data yang sengaja dibuat (agar analisis menghasilkan insight):
  * Seasonality  : lonjakan saat Ramadan/Lebaran (Mar-Apr) & Harbolnas (11.11, 12.12).
  * Channel mix  : offline dominan, online (Shopee/Tokopedia/IG) tumbuh.
  * Repeat buyer : sebagian pelanggan bertransaksi berkali-kali.
  * Pola insight : best-seller jelas, produk margin tipis, dead stock, cabang lemah.
  * Data quality : sedikit duplikat, missing value, & format tanggal beragam
                   (untuk didemokan proses cleaning di load_oltp.py).

Output: file CSV di data/raw/.
"""
from __future__ import annotations

import random
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
from faker import Faker

import config as cfg

fake = Faker("id_ID")
Faker.seed(cfg.RANDOM_SEED)
random.seed(cfg.RANDOM_SEED)
np.random.seed(cfg.RANDOM_SEED)


# --------------------------------------------------------------------------- #
# Helper
# --------------------------------------------------------------------------- #
def _daterange_days(start: str, end: str) -> int:
    d0 = datetime.strptime(start, "%Y-%m-%d").date()
    d1 = datetime.strptime(end, "%Y-%m-%d").date()
    return (d1 - d0).days


def _round_price(x: float) -> int:
    """Bulatkan harga ke kelipatan 500 Rupiah agar terlihat wajar."""
    return int(round(x / 500.0) * 500)


def _season_weight(d: date) -> float:
    """Bobot musiman untuk memilih tanggal transaksi (makin tinggi makin ramai)."""
    w = 1.0
    # Ramadan / menjelang Lebaran (asumsi Mar-Apr)
    if d.month in (3, 4):
        w *= 2.2
    # Harbolnas & akhir tahun
    if d.month == 11:
        w *= 1.4
    if d.month == 12:
        w *= 1.8
    # Puncak tanggal kembar 11.11 & 12.12
    if (d.month, d.day) in ((11, 11), (12, 12)):
        w *= 2.5
    # Akhir pekan sedikit lebih ramai
    if d.weekday() >= 5:
        w *= 1.25
    # Gajian (akhir & awal bulan)
    if d.day >= 25 or d.day <= 3:
        w *= 1.15
    return w


def is_holiday_season(d: date) -> bool:
    return d.month in (3, 4, 11, 12)


# --------------------------------------------------------------------------- #
# 1. Master dimensions
# --------------------------------------------------------------------------- #
def gen_categories() -> pd.DataFrame:
    rows = []
    cid = 1
    for parent, subs in cfg.CATEGORIES.items():
        for sub in subs:
            rows.append({"category_id": cid, "category_name": sub,
                         "parent_category": parent})
            cid += 1
    return pd.DataFrame(rows)


def gen_suppliers() -> pd.DataFrame:
    rows = []
    for i, (name, city, lead) in enumerate(cfg.SUPPLIERS, start=1):
        rows.append({
            "supplier_id": i, "supplier_name": name, "city": city,
            "contact": fake.msisdn()[:12], "lead_time_days": lead,
        })
    return pd.DataFrame(rows)


def gen_stores() -> pd.DataFrame:
    rows = []
    for i, (name, city, prov, stype, open_date) in enumerate(cfg.STORES, start=1):
        rows.append({
            "store_id": i, "store_name": name, "city": city, "province": prov,
            "store_type": stype, "open_date": open_date,
        })
    return pd.DataFrame(rows)


def gen_products(categories: pd.DataFrame, suppliers: pd.DataFrame) -> pd.DataFrame:
    """~180 SKU. Margin bervariasi; sebagian sengaja margin tipis."""
    rows = []
    pid = 1
    n_target = 180
    cat_ids = categories["category_id"].tolist()
    supp_ids = suppliers["supplier_id"].tolist()

    # rentang harga dasar (Rupiah) per parent category
    base_price = {
        "Atasan": (60000, 180000),
        "Bawahan": (90000, 320000),
        "Dress": (120000, 400000),
        "Outerwear": (150000, 500000),
        "Aksesoris": (25000, 150000),
    }
    while pid <= n_target:
        cat = categories.sample(1, random_state=pid).iloc[0]
        parent = cat["parent_category"]
        sub = cat["category_name"]
        lo, hi = base_price[parent]
        sell = _round_price(random.uniform(lo, hi))

        # Margin: mayoritas 35-55%, tapi ~18% produk margin tipis 8-20%
        if random.random() < 0.18:
            margin = random.uniform(0.08, 0.20)
        else:
            margin = random.uniform(0.35, 0.55)
        cost = _round_price(sell * (1 - margin))

        brand = random.choice(cfg.BRANDS)
        size = random.choice(cfg.SIZES)
        color = random.choice(cfg.COLORS)
        sku = f"{parent[:3].upper()}-{brand[:3].upper()}-{pid:04d}"
        name = f"{sub} {brand} {color}"

        rows.append({
            "product_id": pid, "sku": sku, "product_name": name,
            "category_id": int(cat["category_id"]), "brand": brand,
            "size": size, "color": color,
            "cost_price": cost, "sell_price": sell,
            "supplier_id": random.choice(supp_ids), "is_active": True,
        })
        pid += 1
    return pd.DataFrame(rows)


def gen_customers(n: int) -> pd.DataFrame:
    rows = []
    start = datetime.strptime(cfg.DATA_START, "%Y-%m-%d").date()
    for i in range(1, n + 1):
        gender = random.choice(["Pria", "Wanita"])
        name = fake.name_male() if gender == "Pria" else fake.name_female()
        # mayoritas join sebelum periode data, sebagian bergabung di tengah
        join = start - timedelta(days=random.randint(0, 900))
        if random.random() < 0.25:
            join = start + timedelta(days=random.randint(0, 300))
        tier = random.choices(cfg.MEMBER_TIERS, weights=[0.6, 0.3, 0.1])[0]
        rows.append({
            "customer_id": i, "full_name": name, "gender": gender,
            "birth_year": random.randint(1975, 2006),
            "city": random.choice(cfg.CUSTOMER_CITIES),
            "join_date": join.isoformat(), "member_tier": tier,
        })
    df = pd.DataFrame(rows)

    # --- Sengaja sisipkan masalah kualitas data (untuk demo cleaning) ---
    # Missing value pada beberapa kolom non-kritikal
    miss_idx = df.sample(frac=0.03, random_state=1).index
    df.loc[miss_idx, "gender"] = None
    miss_idx2 = df.sample(frac=0.02, random_state=2).index
    df.loc[miss_idx2, "city"] = None
    # Beberapa join_date pakai format berbeda (DD/MM/YYYY)
    alt_idx = df.sample(frac=0.05, random_state=3).index
    df.loc[alt_idx, "join_date"] = pd.to_datetime(
        df.loc[alt_idx, "join_date"]).dt.strftime("%d/%m/%Y")
    return df


# --------------------------------------------------------------------------- #
# 2. Transaksi penjualan + detail
# --------------------------------------------------------------------------- #
def _build_date_pool() -> list[date]:
    """Bangun pool tanggal berbobot musiman untuk sampling transaksi."""
    d0 = datetime.strptime(cfg.DATA_START, "%Y-%m-%d").date()
    n_days = _daterange_days(cfg.DATA_START, cfg.DATA_END) + 1
    pool, weights = [], []
    for i in range(n_days):
        d = d0 + timedelta(days=i)
        pool.append(d)
        weights.append(_season_weight(d))
    weights = np.array(weights)
    weights = weights / weights.sum()
    return pool, weights


def gen_sales(products: pd.DataFrame, customers: pd.DataFrame,
              stores: pd.DataFrame, n_trx: int):
    """Hasilkan sales_transactions & sales_details."""
    date_pool, date_w = _build_date_pool()

    # Popularitas produk mengikuti pola pareto: sedikit produk sangat laris
    prod = products.copy()
    pop = np.random.pareto(1.5, len(prod)) + 0.1
    # ~12% produk dijadikan "dead stock" (popularitas ~0)
    dead_idx = prod.sample(frac=0.12, random_state=7).index
    pop[prod.index.get_indexer(dead_idx)] = 0.002
    prod_weight = pop / pop.sum()

    # Bobot cabang: flagship Jakarta dominan, satu cabang sengaja lemah (Medan)
    store_ids = stores["store_id"].tolist()
    store_w = {sid: 1.0 for sid in store_ids}
    store_w[1] = 3.0            # Jakarta flagship
    store_w[2] = 2.0            # Bandung
    store_w[5] = 0.5            # Medan (underperform)
    sw = np.array([store_w[s] for s in store_ids], dtype=float)
    sw = sw / sw.sum()

    # --- Rencana penugasan pelanggan dengan distribusi pembelian terkontrol ---
    # Tujuan: repeat-rate realistis (~35-40%). Sebagian besar pelanggan membeli
    # sekali; sebagian menjadi repeat buyer (2..n kali).
    cust_ids = customers["customer_id"].tolist()
    n_guest = int(n_trx * 0.10)
    n_named = n_trx - n_guest
    purchase_counts = [1, 2, 3, 4, 6, 10]
    count_weights = [0.62, 0.20, 0.10, 0.05, 0.02, 0.01]  # mean ~1.6
    assign_pool: list[int] = []
    ci = 0
    rng = random.Random(cfg.RANDOM_SEED)
    while len(assign_pool) < n_named and ci < len(cust_ids):
        k = rng.choices(purchase_counts, weights=count_weights)[0]
        assign_pool.extend([cust_ids[ci]] * k)
        ci += 1
    assign_pool = assign_pool[:n_named]
    rng.shuffle(assign_pool)
    # Barisan flag guest/named yang diacak
    is_named_seq = [True] * n_named + [False] * n_guest
    rng.shuffle(is_named_seq)
    named_iter = iter(assign_pool)

    prod_ids = prod["product_id"].to_numpy()
    prod_lookup = prod.set_index("product_id")[["sell_price", "cost_price"]].to_dict("index")

    trx_rows, det_rows = [], []
    detail_id = 1

    trx_dates = np.random.choice(len(date_pool), size=n_trx, p=date_w)
    trx_stores = np.random.choice(store_ids, size=n_trx, p=sw)
    trx_channels = np.random.choice(cfg.CHANNELS, size=n_trx, p=cfg.CHANNEL_WEIGHTS)

    for t in range(1, n_trx + 1):
        d = date_pool[trx_dates[t - 1]]
        store_id = int(trx_stores[t - 1])
        channel = trx_channels[t - 1]

        # Penugasan pelanggan dari rencana (guest vs named sudah diacak)
        if is_named_seq[t - 1]:
            customer_id = int(next(named_iter))
        else:
            customer_id = None

        # jumlah item per transaksi (1-5, mayoritas 1-2)
        n_items = random.choices([1, 2, 3, 4, 5], weights=[0.45, 0.28, 0.15, 0.08, 0.04])[0]
        chosen = np.random.choice(prod_ids, size=n_items, replace=False, p=prod_weight)

        gross = 0.0
        line_buffer = []
        for pidv in chosen:
            info = prod_lookup[int(pidv)]
            qty = random.choices([1, 2, 3], weights=[0.7, 0.22, 0.08])[0]
            unit_price = float(info["sell_price"])
            unit_cost = float(info["cost_price"])
            line_total = unit_price * qty
            gross += line_total
            line_buffer.append((int(pidv), qty, unit_price, unit_cost, line_total))

        # Diskon: lebih sering & lebih besar saat musim ramai
        base_disc_prob = 0.35 if is_holiday_season(d) else 0.15
        discount = 0.0
        if random.random() < base_disc_prob:
            disc_pct = random.uniform(0.05, 0.30 if is_holiday_season(d) else 0.15)
            discount = round(gross * disc_pct, 2)
        total = round(gross - discount, 2)

        trx_rows.append({
            "transaction_id": t, "store_id": store_id, "customer_id": customer_id,
            "channel": channel, "transaction_date": d.isoformat(),
            "payment_method": random.choice(cfg.PAYMENT_METHODS),
            "total_amount": total, "discount_amount": discount,
        })
        for (pidv, qty, up, uc, lt) in line_buffer:
            det_rows.append({
                "detail_id": detail_id, "transaction_id": t, "product_id": pidv,
                "quantity": qty, "unit_price": up, "unit_cost": uc, "line_total": lt,
            })
            detail_id += 1

    trx = pd.DataFrame(trx_rows)
    det = pd.DataFrame(det_rows)

    # --- Sengaja sisipkan duplikat baris detail (untuk demo dedup) ---
    dup = det.sample(frac=0.005, random_state=9).copy()
    det = pd.concat([det, dup], ignore_index=True)

    return trx, det, dead_idx


# --------------------------------------------------------------------------- #
# 3. Purchase orders + inventory movements
# --------------------------------------------------------------------------- #
def gen_purchasing_and_inventory(products: pd.DataFrame, stores: pd.DataFrame,
                                 suppliers: pd.DataFrame, sales_details: pd.DataFrame,
                                 sales_trx: pd.DataFrame):
    """Bangun PO, detail PO, dan ledger inventory berbasis demand.

    Prinsip: total stok masuk (in) >= total terjual per (produk, toko) sehingga
    saldo stok TIDAK PERNAH negatif, dan sisa stok akhir = 'target ending stock'
    yang diacak (0.3-3 bulan penjualan) -> menghasilkan campuran realistis antara
    produk yang perlu restock dan yang aman, plus dead stock untuk produk tak laku.
    """
    po_rows, po_det_rows, inv_rows = [], [], []
    po_id, po_det_id, mov_id = 1, 1, 1

    cost_of = products.set_index("product_id")["cost_price"].to_dict()
    supp_of = products.set_index("product_id")["supplier_id"].to_dict()
    d0 = datetime.strptime(cfg.DATA_START, "%Y-%m-%d").date()

    # Terjual per (store, product) — buang duplikat detail dulu
    det = sales_details.drop_duplicates(subset=["detail_id"]).merge(
        sales_trx[["transaction_id", "store_id", "transaction_date"]],
        on="transaction_id", how="left")
    sold_ps = (det.groupby(["store_id", "product_id"])["quantity"].sum().to_dict())

    # --- Stok masuk awal (PO diterima sebelum periode) per (toko, produk) ---
    for store_id in stores["store_id"]:
        for pid in products["product_id"]:
            sold = int(sold_ps.get((store_id, pid), 0))
            avg_month = sold / 12.0
            if sold == 0:
                end_target = random.randint(10, 60)      # dead stock mengendap
            else:
                # sisa stok 0.3-3.0 bulan penjualan (campuran urgent s/d aman)
                end_target = max(1, int(round(avg_month * random.uniform(0.3, 3.0))))
            init_qty = sold + end_target                 # jamin saldo akhir positif

            # Diterima selalu SEBELUM periode agar saldo stok tidak pernah negatif
            order_date = d0 - timedelta(days=random.randint(15, 28))
            recv_date = order_date + timedelta(days=random.randint(1, 7))
            cost = cost_of[pid]
            po_rows.append({
                "po_id": po_id, "supplier_id": int(supp_of[pid]),
                "store_id": int(store_id), "order_date": order_date.isoformat(),
                "received_date": recv_date.isoformat(), "status": "received",
                "total_cost": round(cost * init_qty, 2),
            })
            po_det_rows.append({
                "po_detail_id": po_det_id, "po_id": po_id, "product_id": int(pid),
                "quantity": init_qty, "unit_cost": cost,
            })
            inv_rows.append({
                "movement_id": mov_id, "store_id": int(store_id), "product_id": int(pid),
                "movement_date": recv_date.isoformat(), "movement_type": "in",
                "quantity": init_qty, "reference": f"PO#{po_id}",
            })
            po_id += 1
            po_det_id += 1
            mov_id += 1

    # --- Stock OUT dari penjualan (tanggal transaksi) ---
    for _, r in det.iterrows():
        inv_rows.append({
            "movement_id": mov_id, "store_id": int(r["store_id"]),
            "product_id": int(r["product_id"]),
            "movement_date": r["transaction_date"], "movement_type": "out",
            "quantity": -int(r["quantity"]),
            "reference": f"TRX#{int(r['transaction_id'])}",
        })
        mov_id += 1

    return (pd.DataFrame(po_rows), pd.DataFrame(po_det_rows), pd.DataFrame(inv_rows))


def gen_campaigns() -> pd.DataFrame:
    rows = [
        ("Ramadan Sale", "shopee", "2026-03-10", "2026-04-05", 15000000, 20),
        ("Lebaran Fashion Week", "offline", "2026-03-25", "2026-04-10", 25000000, 15),
        ("Harbolnas 11.11", "tokopedia", "2025-11-05", "2025-11-13", 20000000, 25),
        ("Harbolnas 12.12", "shopee", "2025-12-05", "2025-12-14", 22000000, 30),
        ("Instagram Flash Sale", "instagram", "2025-09-01", "2025-09-07", 8000000, 18),
        ("Year End Clearance", "offline", "2025-12-20", "2026-01-05", 12000000, 35),
    ]
    return pd.DataFrame([
        {"campaign_id": i + 1, "campaign_name": n, "channel": c,
         "start_date": s, "end_date": e, "budget": b, "discount_pct": d}
        for i, (n, c, s, e, b, d) in enumerate(rows)
    ])


# --------------------------------------------------------------------------- #
# Orkestrasi generate
# --------------------------------------------------------------------------- #
def main() -> None:
    cfg.RAW_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[generate] Membuat synthetic dataset -> {cfg.RAW_DIR}")

    categories = gen_categories()
    suppliers = gen_suppliers()
    stores = gen_stores()
    products = gen_products(categories, suppliers)
    customers = gen_customers(cfg.N_CUSTOMERS)
    campaigns = gen_campaigns()

    sales_trx, sales_det, dead_idx = gen_sales(
        products, customers, stores, cfg.N_TRANSACTIONS)

    po, po_det, inv = gen_purchasing_and_inventory(
        products, stores, suppliers, sales_det, sales_trx)

    tables = {
        "categories": categories,
        "suppliers": suppliers,
        "stores": stores,
        "products": products,
        "customers": customers,
        "sales_transactions": sales_trx,
        "sales_details": sales_det,
        "purchase_orders": po,
        "po_details": po_det,
        "inventory_movements": inv,
        "marketing_campaigns": campaigns,
    }
    for name, df in tables.items():
        path = cfg.RAW_DIR / f"{name}.csv"
        df.to_csv(path, index=False)
        print(f"  - {name:22s}: {len(df):>7,} baris -> {path.name}")

    print(f"[generate] Selesai. {len(products)} produk "
          f"({len(dead_idx)} di antaranya dead stock), "
          f"{len(customers)} pelanggan, {len(sales_trx):,} transaksi.")


if __name__ == "__main__":
    main()

# Business Case — BI Platform untuk UMKM Fashion "Rumah Mode Nusantara"

## 1. Latar Belakang Masalah

Banyak UMKM fashion di Indonesia sudah mencatat transaksi (POS, marketplace, pembukuan
Excel), tetapi **data tersebut tidak pernah diolah menjadi keputusan**. Owner umumnya
menghadapi masalah klasik:

| Masalah | Dampak Bisnis |
|---------|---------------|
| Tidak tahu produk mana yang benar-benar menghasilkan **profit** (bukan sekadar laku) | Modal habis di produk margin tipis |
| **Stok tidak seimbang** — produk laris cepat habis, produk lain menumpuk | Kehilangan penjualan + modal mengendap (*dead stock*) |
| Tidak ada visibilitas performa **antar cabang & channel** | Cabang/channel rugi dibiarkan berjalan |
| Tidak paham perilaku **pelanggan** (repeat vs one-time) | Budget promosi tidak tepat sasaran |
| Keputusan restock berdasarkan "feeling" | Over/under-stock, cash flow terganggu |

**Tujuan platform:** mengubah data transaksi mentah menjadi *dashboard* dan *insight*
yang bisa langsung dipakai owner untuk keputusan penjualan, stok, dan pemasaran.

## 2. User Persona

| Persona | Kebutuhan Utama | Halaman Dashboard |
|---------|-----------------|-------------------|
| **Owner / Pemilik** | Gambaran besar bisnis: revenue, profit, margin, tren | Executive Overview |
| **Store Manager** | Performa cabang, channel, pola penjualan harian | Sales Performance, Branch Performance |
| **Finance** | Margin, profitabilitas produk & kategori, AOV | Executive Overview, Product & Category |
| **Inventory Staff** | Stok menipis, dead stock, rekomendasi restock | Inventory & Restock |
| **Marketing** | Segmentasi pelanggan, repeat rate, demografi | Customer Analysis |

## 3. KPI Utama

| KPI | Definisi | Kenapa Penting |
|-----|----------|----------------|
| **Revenue** | Total penjualan bersih (setelah diskon) | Ukuran skala bisnis |
| **Gross Profit** | Revenue − COGS (harga modal) | Laba kotor sesungguhnya |
| **Gross Margin %** | Gross Profit ÷ Revenue × 100 | Efisiensi/kesehatan harga |
| **Average Order Value (AOV)** | Revenue ÷ jumlah transaksi | Nilai belanja rata-rata |
| **Repeat Customer Rate** | % pelanggan dengan > 1 transaksi | Loyalitas & retensi |
| **Stock Turnover** | COGS ÷ rata-rata stok | Kecepatan perputaran barang |
| **Low-Stock Alert** | Produk dengan stok < 1 bulan penjualan | Cegah kehabisan barang laris |
| **Best-Selling Product** | Produk dengan unit terjual tertinggi | Fokus stok & promosi |
| **Dead Stock** | Produk terjual ≤ 5 unit/tahun namun masih ada stok | Modal mengendap |

## 4. Scope Data

- **Periode:** 12 bulan (Juli 2025 – Juni 2026)
- **Cabang:** 6 toko di Jakarta, Bandung, Surabaya, Yogyakarta, Medan, Semarang
- **Channel:** Offline (toko fisik), Shopee, Tokopedia, Instagram
- **Volume:** ±20.000 transaksi, ±180 SKU, ±12.000 pelanggan
- **Domain:** Fashion & apparel (atasan, bawahan, dress, outerwear, aksesoris) dengan
  atribut khas fashion: **ukuran, warna, brand**, serta musiman **Ramadan/Lebaran** dan
  **Harbolnas (11.11 / 12.12)**.

## 5. Pertanyaan Bisnis yang Dijawab

1. Produk apa yang paling laris dan paling menguntungkan?
2. Produk mana yang *revenue*-nya tinggi tapi *margin*-nya rendah?
3. Cabang mana yang berkinerja terbaik dan terburuk?
4. Siapa pelanggan paling loyal, dan berapa *repeat rate*-nya?
5. Produk apa yang *slow moving / dead stock*?
6. Produk apa yang perlu segera di-*restock*?
7. Bagaimana tren penjualan bulanan (musiman)?
8. Channel penjualan mana yang paling efektif?

Jawaban atas pertanyaan-pertanyaan ini tersedia dalam bentuk SQL (`sql/analytics/`),
dashboard interaktif (`dashboard/`), dan laporan insight ([03_insight_report.md](03_insight_report.md)).

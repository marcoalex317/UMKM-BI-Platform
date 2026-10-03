# End-to-End Retail BI Platform untuk UMKM Indonesia

Proyek ini saya buat untuk mempraktikkan alur kerja BI dari awal sampai akhir
pada sebuah chain fashion UMKM fiktif bernama **Rumah Mode Nusantara**. Saya
merancang database transaksional, membangun data warehouse dengan star schema,
menulis ETL pipeline di Python, menjawab pertanyaan bisnis dengan SQL, lalu
menyajikannya dalam dashboard Streamlit enam halaman.

Datanya saya bangkitkan sendiri dengan Faker, lengkap dengan atribut khas fashion
(ukuran, warna, brand) dan pola musim belanja Indonesia seperti Ramadan, Lebaran,
dan Harbolnas.

![Halaman Executive Overview](assets/screenshots/01-executive-overview.png)

## Pertanyaan yang ingin dijawab

Pemilik UMKM fashion biasanya punya banyak data transaksi, tapi jarang
memakainya untuk mengambil keputusan. Saya membatasi analisis pada delapan
pertanyaan:

1. Produk apa yang paling laris dan paling menguntungkan?
2. Produk mana yang revenue-nya tinggi tapi margin-nya rendah?
3. Cabang mana yang terbaik dan terburuk?
4. Seberapa loyal pelanggan, dan berapa repeat rate-nya?
5. Produk mana yang tidak laku dan menahan modal?
6. Produk mana yang perlu segera di-restock?
7. Bagaimana pola penjualan sepanjang tahun?
8. Channel penjualan mana yang paling efektif?

Latar belakang lengkapnya ada di [docs/01_business_case.md](docs/01_business_case.md).

## Apa yang saya temukan

Total revenue dalam 12 bulan adalah Rp 9,28 miliar dengan margin 38,4%. Secara
umum bisnisnya sehat, tapi ada beberapa hal yang menahan profit dan kas:

- **Rp 411 juta modal tertahan di 22 SKU yang hampir tidak laku**, atau 32% dari
  seluruh nilai stok.
- **25 SKU bermargin tipis menyerap 12,4% revenue tapi cuma menyumbang 3,1%
  gross profit.** Satu topi yang laris bahkan hanya bermargin 6,1% setelah diskon.
- **39% revenue setahun terjadi di tiga bulan saja**: Maret dan April saat
  Ramadan, serta Desember saat Harbolnas.
- **Satu produk, Rok Senja Label Abu-abu, menyumbang 9% revenue.**
- **Cabang Medan hanya menghasilkan sekitar seperenam dari Jakarta**, dan separuh
  dari cabang reguler terlemah lainnya.
- **Channel online sudah 51% revenue**, dengan nilai transaksi rata-rata yang
  sedikit lebih tinggi dari offline.
- **Tier member belum membedakan pelanggan.** Rata-rata belanja per orang hampir
  sama di Bronze, Silver, dan Gold.

## Dampak bisnis

Saya menghitung dampak rekomendasi utama langsung dari data warehouse dengan
asumsi yang sengaja konservatif:

| Rekomendasi | Perkiraan dampak |
|---|---|
| Clearance 22 SKU dead stock dengan diskon 30 sampai 50% | Kas masuk Rp 349 sampai 488 juta, sekali jalan |
| Turunkan harga beli 25 SKU margin tipis sebesar 5% | +Rp 51,9 juta gross profit per tahun |
| Naikkan revenue Medan ke level cabang Yogyakarta | +Rp 204,8 juta gross profit per tahun |
| Naikkan repeat rate dari 38,2% ke 43,2% | +Rp 176,5 juta gross profit per tahun |

Tiga rekomendasi yang berulang tiap tahun totalnya sekitar Rp 433 juta, atau 12%
dari gross profit sekarang. Sepuluh temuan lengkap beserta asumsi, risiko, dan
rekomendasinya ada di [docs/03_insight_report.md](docs/03_insight_report.md).

## Arsitektur

```mermaid
flowchart LR
    A["generate_data.py<br/>Faker + logika bisnis"] --> B[("CSV<br/>data/raw")]
    B --> C["load_oltp.py<br/>cleaning"]
    C --> D[("OLTP DB<br/>SQLite/PostgreSQL")]
    D --> E["transform_dwh.py"]
    E --> F[("Star Schema DWH")]
    F --> G["SQL Analytics"]
    F --> H["Streamlit Dashboard"]
    F --> I["Power BI"]
    G --> J["Insight Report"]
```

Di akhir proses transformasi, pipeline membandingkan total net revenue di
database transaksional dengan di data warehouse. Kalau ada selisih, berarti ada
data yang hilang atau terduplikasi di tengah jalan. Hasil terakhir:

```
Rekonsiliasi net revenue: OLTP=9,280,562,435 vs DWH=9,280,562,435 (selisih 0)
```

Diagram lengkapnya ada di [docs/architecture.md](docs/architecture.md).

## Struktur database

- **Database transaksional:** 11 tabel yang sudah dinormalisasi. Lihat
  [ERD](docs/erd_oltp.md).
- **Data warehouse:** star schema dengan dua tabel fakta (`fact_sales` dan
  `fact_inventory`) serta lima dimensi. Lihat [star schema](docs/star_schema.md).
- **Kamus data:** [docs/02_data_dictionary.md](docs/02_data_dictionary.md).

## Tools

Python 3.10 ke atas dan SQL. Database utamanya PostgreSQL, dengan SQLite sebagai
pilihan default supaya proyek bisa dijalankan tanpa setup apa pun. ETL memakai
pandas, NumPy, Faker, dan SQLAlchemy. Dashboard dibuat dengan Streamlit dan
Plotly, dan ada panduan untuk membangun versi Power BI-nya. Dokumentasi ditulis
dalam Markdown dengan diagram Mermaid.

## Dashboard

Ada enam halaman, dan masing-masing ditutup dengan satu kotak insight. Empat
halaman punya filter periode, cabang, dan channel di sidebar. Halaman inventori
dan pelanggan menampilkan data keseluruhan tanpa filter.

**Executive Overview** menampilkan KPI utama (revenue, gross profit, margin,
nilai transaksi rata-rata, repeat rate), tren bulanan, dan kontribusi tiap
kategori. Tampilannya ada di bagian atas README ini.

**Sales Performance** menunjukkan tren harian, perbandingan channel, metode
pembayaran, dan pola penjualan per hari dalam seminggu.

![Halaman Sales Performance](assets/screenshots/02-sales-performance.png)

**Product & Category** berisi produk terlaris, produk dengan margin tertinggi,
analisis Pareto per kategori, serta penjualan per ukuran dan warna.

![Halaman Product & Category](assets/screenshots/03-product-category.png)

**Inventory & Restock** menampilkan nilai stok, produk yang hampir habis,
dead stock, dan daftar prioritas restock.

![Halaman Inventory & Restock](assets/screenshots/04-inventory-restock.png)

**Customer Analysis** membahas repeat rate, tier member, segmentasi RFM
sederhana, demografi, dan pelanggan teratas.

![Halaman Customer Analysis](assets/screenshots/05-customer-analysis.png)

**Branch Performance** membandingkan dan meranking keenam cabang, termasuk
komposisi channel dan tren bulanan per cabang.

![Halaman Branch Performance](assets/screenshots/06-branch-performance.png)

## Cara menjalankan

Seluruh pipeline selesai dalam sekitar 8 detik dan memakai SQLite, jadi tidak
perlu menyiapkan database.

```bash
pip install -r requirements.txt
python etl/run_pipeline.py
streamlit run dashboard/streamlit_app.py
```

Untuk memakai PostgreSQL, salin `.env.example` menjadi `.env`, isi
`DB_ENGINE=postgres` beserta kredensialnya, lalu jalankan ulang dua perintah
terakhir. Skema tabelnya ada di `sql/oltp/` dan `sql/warehouse/`.

## Struktur folder

```
UMKM-BI-Platform/
├── docs/            # business case, kamus data, insight report, ERD, diagram
├── sql/             # skema database transaksional, skema warehouse, query analitik
├── etl/             # generate, load, dan transform (dijalankan lewat run_pipeline.py)
├── data/            # CSV mentah dan database SQLite (dibuat saat pipeline jalan)
├── dashboard/       # aplikasi Streamlit enam halaman dan panduan Power BI
└── assets/          # screenshot dashboard
```

## Keterbatasan

- **Datanya sintetis.** Semua transaksi dibangkitkan dengan Faker memakai seed
  tetap, jadi angkanya selalu sama setiap kali pipeline dijalankan. Pola seperti
  puncak Ramadan memang dirancang di generator. Proyek ini menunjukkan cara
  menganalisis, bukan kondisi toko yang sebenarnya.
- **Tidak ada biaya operasional cabang**, jadi analisis berhenti di gross profit
  dan profitabilitas per cabang belum bisa dinilai.
- **Sekitar 10% revenue berasal dari pembeli non-member**, sehingga analisis
  tier, usia, dan repeat rate hanya mencakup member.
- **Tidak ada data stok habis**, jadi penjualan yang hilang karena kehabisan
  barang tidak bisa dihitung.

## Rencana pengembangan

- Menerapkan SCD Type 2 di `dim_product` dan `dim_customer` untuk melacak
  perubahan harga dan tier.
- Menjadwalkan pipeline dengan Airflow atau Dagster, dengan incremental load.
- Menambahkan tes kualitas data dengan Great Expectations atau dbt.
- Membuat forecasting permintaan dengan Prophet atau ARIMA untuk rekomendasi
  restock.
- Men-deploy dashboard ke Streamlit Community Cloud.

## Tentang saya

Marco Alexander, mahasiswa Sistem Informasi di BINUS University dengan fokus
Business Intelligence.
[linkedin.com/in/marcolex](https://linkedin.com/in/marcolex)

# Insight Report: Rumah Mode Nusantara (12 Bulan)

Analisis ini memakai data warehouse dari sekitar 20.000 transaksi selama
Juli 2025 sampai Juni 2026. Dalam periode itu toko menghasilkan **revenue
Rp 9,28 miliar** dan **gross profit Rp 3,56 miliar**, dengan **margin 38,4%**.

Semua angka di laporan ini bisa dihasilkan ulang dengan menjalankan
`python etl/run_pipeline.py`, karena data dibangkitkan dengan seed tetap.

---

## Ringkasan Eksekutif

Secara keseluruhan bisnis ini sehat: margin 38,4% dan revenue tersebar di enam
cabang serta empat channel. Masalahnya ada di beberapa titik yang diam-diam
menahan profit dan kas.

- **Rp 411 juta modal tertahan di 22 SKU yang hampir tidak laku.** Itu 32% dari
  seluruh nilai stok.
- **25 SKU bermargin tipis menyerap 12,4% revenue tapi hanya menyumbang 3,1%
  gross profit.** Setelah diskon, margin riilnya tinggal 9,6%.
- **39% revenue setahun terjadi hanya dalam tiga bulan** (Maret, April,
  Desember). Kesalahan stok di musim puncak berarti kehilangan bagian besar
  pendapatan tahunan.
- **Cabang Medan menghasilkan sekitar seperenam dari Jakarta** dan separuh dari
  cabang reguler terlemah lainnya.
- **Program tier member belum membedakan pelanggan bernilai.** Rata-rata belanja
  per pelanggan hampir sama di Bronze, Silver, dan Gold.

Kalau tiga rekomendasi utama dijalankan dengan asumsi yang konservatif,
perkiraan tambahannya sekitar **Rp 433 juta gross profit per tahun** (sekitar
12% dari gross profit sekarang), ditambah **Rp 349 sampai 488 juta kas** dari
penjualan sekali jalan stok yang mengendap. Rincian dan asumsinya ada di bagian
Dampak Bisnis.

---

## Temuan dan Rekomendasi

### 1. Penjualan sangat bergantung pada Ramadan dan Harbolnas
Bulan tertinggi adalah **Maret 2026 (Rp 1,31 M)** dan **April 2026 (Rp 1,21 M)**
saat Ramadan dan Lebaran, disusul **Desember 2025 (Rp 1,12 M)** saat Harbolnas
12.12. Rata-rata ketiga bulan ini sekitar 2 kali bulan biasa (Rp 602 juta), dan
bersama-sama menyumbang **39,2% revenue setahun**.
> **Aksi:** Siapkan stok dan kas 4 sampai 6 minggu sebelum Ramadan dan Harbolnas.
> Pusatkan sebagian besar budget kampanye di Februari sampai April dan November
> sampai Desember.

### 2. Satu produk menyumbang 9% revenue
**Rok Senja Label Abu-abu** menghasilkan **Rp 844 juta**, sekitar 9,1% dari
seluruh revenue, hanya dari satu SKU. Produk terlaris berikutnya adalah Gamis
Rimba Co. Putih (Rp 548 juta) dan Topi Nusantara Basic Putih (3.449 unit).
> **Aksi:** Amankan pasokan produk ini lewat kontrak supplier dan safety stock
> yang lebih tinggi. Kembangkan dua atau tiga produk lain supaya bisnis tidak
> bergantung pada satu SKU.

### 3. Ada produk laris yang hampir tidak menghasilkan untung
Saya menandai 25 SKU dengan margin harga jual di bawah 25%. Semuanya menghasilkan
**Rp 1,15 miliar revenue (12,4% dari total)**, tapi gross profit-nya hanya
**Rp 111 juta (3,1% dari total)**. Contoh paling jelas adalah **Topi Rimba Co.
Putih**: revenue Rp 240 juta, margin harga jualnya 9,7%, dan setelah diskon
margin riilnya tinggal **6,1%**. Beberapa Celana Kulot dan Blazer ada di kisaran
margin harga jual 12 sampai 19%.
> **Aksi:** Negosiasi ulang harga beli ke supplier, naikkan harga jual bertahap,
> atau jual sebagai paket dengan produk bermargin tinggi.

### 4. Cabang Medan jauh tertinggal
**RMN Medan Sunggal** hanya menghasilkan **Rp 542 juta**, sekitar 6 kali lebih
kecil dari flagship Jakarta (Rp 3,31 M). Perbandingan yang lebih adil adalah
dengan sesama cabang reguler: Medan juga cuma separuh dari cabang reguler terlemah
berikutnya, Yogyakarta (Rp 1,08 M). Data ini tidak memuat biaya sewa dan gaji per
cabang, jadi belum bisa dipastikan apakah Medan rugi atau sekadar kecil.
> **Aksi:** Audit cabang Medan (lokasi, staf, ragam stok) dan kumpulkan biaya
> operasionalnya. Dorong penjualan online untuk wilayah sekitarnya. Kalau dalam
> dua kuartal tidak membaik, nilai ulang kelayakan cabang dengan data biaya
> tersebut.

### 5. Rp 411 juta modal tertahan di stok yang tidak laku
**22 SKU** terjual 5 unit atau kurang dalam setahun, padahal stoknya masih ada.
Nilainya **Rp 411 juta** dengan harga pokok, atau **32,4% dari seluruh nilai
stok** (Rp 1,27 M). Kas sebesar itu tertidur di gudang.
> **Aksi:** Jalankan clearance sale atau diskon bertahap, jual sebagai paket
> dengan produk terlaris, dan hentikan restock SKU ini.

### 6. Channel online sudah menyumbang separuh revenue
Offline menghasilkan **Rp 4,58 M (49,4%)**, sementara Shopee, Tokopedia, dan
Instagram bersama-sama **Rp 4,70 M (50,6%)**. Nilai rata-rata transaksi online
(Shopee Rp 479 ribu) sedikit lebih tinggi dari offline (Rp 458 ribu), dengan
margin yang setara di sekitar 38%.
> **Aksi:** Perkuat kanal online lewat konten Instagram serta iklan Shopee dan
> Tokopedia. Kanal ini terbukti sama menguntungkannya dan bisa menjangkau kota
> yang tidak punya cabang.

### 7. Bawahan dan Dress adalah sumber profit utama
**Bawahan (Rp 2,76 M, margin 39,7%)** dan **Dress (Rp 2,03 M, margin 39,4%)**
memimpin di revenue sekaligus margin. Atasan dan Aksesoris bermargin lebih rendah
di sekitar 36,7%.
> **Aksi:** Tambah varian ukuran dan warna di Bawahan dan Dress. Untuk Atasan dan
> Aksesoris, evaluasi harga beli atau posisikan sebagai produk tambahan untuk
> menaikkan nilai transaksi.

### 8. Repeat rate 38%, dan pelanggan repeat bernilai hampir 3 kali lipat
Dari 10.332 member yang bertransaksi, **38,2%** membeli lebih dari sekali.
Pelanggan repeat rata-rata belanja **Rp 1,36 juta** setahun, dibanding
**Rp 468 ribu** untuk pelanggan yang hanya membeli sekali.
> **Aksi:** Bangun program loyalitas (poin, voucher ulang tahun, penawaran
> pembelian kedua) untuk mengubah pembeli sekali menjadi pelanggan repeat.

### 9. Tier member belum mencerminkan nilai pelanggan
Bronze menyumbang revenue terbesar (**Rp 5,02 M**), disusul Silver (Rp 2,52 M)
dan Gold (Rp 823 juta). Tapi itu terutama karena 60% member ada di Bronze. Kalau
dihitung per orang, rata-rata belanja setahun hampir sama di ketiga tier: Bronze
Rp 807 ribu, Silver Rp 823 ribu, Gold Rp 784 ribu. Frekuensi belanjanya juga
mirip, sekitar 1,7 transaksi per orang.
> **Aksi:** Tinjau ulang kriteria dan benefit tiap tier. Sekarang tier lebih
> tinggi tidak diikuti belanja yang lebih tinggi, jadi benefit Gold diberikan
> tanpa imbal balik yang terlihat.

### 10. Usia 20 sampai 49 tahun hampir sama besar, usia 50+ tertinggal
Kelompok **40-49 (Rp 2,65 M)**, **30-39 (Rp 2,60 M)**, dan **20-29 (Rp 2,59 M)**
masing-masing menyumbang sekitar 31% revenue member. Segmen 50+ hanya 6,2%.
> **Aksi:** Pertahankan koleksi yang menjangkau rentang 20 sampai 49 tahun. Uji
> koleksi khusus dalam skala kecil untuk melihat apakah segmen 50+ bisa diperbesar.

---

## Risiko dan Implikasi

**Konsentrasi musim.** 39,2% revenue terjadi dalam tiga bulan. Keterlambatan
pasokan atau salah prediksi stok di satu musim puncak bisa menggerus sebagian
besar pendapatan tahunan, dan arus kas di bulan biasa harus cukup untuk menutup
pembelian stok menjelang musim tersebut.

**Ketergantungan pada satu SKU.** Kalau supplier Rok Senja Label bermasalah,
sekitar 9% revenue ikut terancam tanpa produk pengganti yang setara.

**Margin yang mudah berubah jadi rugi.** Beberapa SKU sudah bermargin riil 4,5
sampai 6,1% setelah diskon. Kenaikan harga beli yang kecil saja bisa membuat
produk ini dijual di bawah harga pokok.

**Kas yang tertahan.** Rp 411 juta di dead stock adalah sepertiga nilai stok.
Makin lama dibiarkan, makin besar diskon yang dibutuhkan untuk menjualnya,
terutama untuk produk fashion yang mengikuti tren.

**Keputusan cabang tanpa data biaya.** Menutup atau mempertahankan Medan hanya
berdasarkan revenue berisiko salah, karena biaya operasional cabang belum ada di
data.

**Benefit member tanpa hasil.** Kalau tier Gold dan Silver mendapat diskon atau
benefit lebih, sementara belanjanya tidak lebih tinggi, program ini mengurangi
margin tanpa menaikkan loyalitas.

---

## Dampak Bisnis

Saya menghitung dampak empat rekomendasi utama langsung dari data warehouse.
Setiap angka memakai asumsi yang sengaja dibuat konservatif dan dituliskan di
kolom kedua.

| Rekomendasi | Asumsi | Perkiraan dampak |
|---|---|---|
| Clearance 22 SKU dead stock | Dijual dengan diskon 30 sampai 50% dari harga jual | Kas masuk **Rp 349 sampai 488 juta**, sekali jalan. Diskon sampai 41% masih menutup harga pokok |
| Turunkan harga beli 25 SKU margin tipis | Negosiasi supplier turun 5%, volume tetap | **+Rp 51,9 juta** gross profit per tahun (Rp 103,8 juta kalau turun 10%) |
| Naikkan cabang Medan | Revenue Medan mencapai level Yogyakarta, margin tetap 38,4% | **+Rp 533,5 juta** revenue dan **+Rp 204,8 juta** gross profit per tahun |
| Naikkan repeat rate 5 poin | 517 pembeli sekali menjadi pelanggan repeat, dengan selisih gross profit Rp 341 ribu per orang | **+Rp 176,5 juta** gross profit per tahun |

Tiga rekomendasi yang berulang setiap tahun (harga beli, Medan, repeat rate)
totalnya sekitar **Rp 433 juta gross profit per tahun**, atau 12% dari gross
profit sekarang. Clearance dead stock terpisah karena hanya terjadi sekali dan
dampaknya berupa kas, bukan profit.

Musim puncak tidak saya masukkan ke tabel. Data tidak mencatat kejadian stok
habis, jadi penjualan yang hilang tidak bisa dihitung. Yang bisa ditunjukkan
adalah besarnya taruhan: Rp 3,64 miliar revenue bergantung pada kesiapan stok di
tiga bulan itu.

---

## Ringkasan Rekomendasi Prioritas

| Prioritas | Aksi | Dampak |
|---|---|---|
| Tinggi | Clearance dead stock Rp 411 juta | Kas Rp 349 sampai 488 juta |
| Tinggi | Perbaiki harga beli produk margin tipis | +Rp 51,9 juta GP per tahun |
| Sedang | Audit cabang Medan dan kumpulkan data biayanya | Sampai +Rp 204,8 juta GP per tahun |
| Sedang | Stok dan kampanye khusus Ramadan dan Harbolnas | Melindungi Rp 3,64 M revenue musim puncak |
| Lanjutan | Program loyalitas dan desain ulang tier member | +Rp 176,5 juta GP per tahun |

---

## Keterbatasan

- **Data ini sintetis.** Semua transaksi dibangkitkan dengan library Faker
  (seed 42) di `etl/generate_data.py`. Pola seperti puncak Ramadan dan Harbolnas
  memang dirancang di generator. Laporan ini menunjukkan cara menganalisis,
  bukan kondisi toko yang sebenarnya.
- **Tidak ada biaya operasional cabang** seperti sewa dan gaji, jadi analisis
  berhenti di gross profit dan profitabilitas per cabang tidak bisa dinilai.
- **9,9% revenue (Rp 917 juta dari 2.000 transaksi) berasal dari non-member.**
  Analisis tier, usia, dan repeat rate hanya mencakup revenue member sebesar
  Rp 8,36 miliar.
- **Tidak ada data stok habis atau penjualan yang hilang**, sehingga dampak
  kekurangan stok hanya bisa ditunjukkan sebagai besarnya risiko.
- **Skenario dampak memakai asumsi sederhana.** Volume dianggap tetap saat harga
  beli turun, dan reaksi pelanggan terhadap perubahan harga tidak diperhitungkan.
- **Periode hanya 12 bulan**, jadi pola musiman baru terlihat sekali dan belum
  bisa dibandingkan antar tahun.
- **Batas dead stock (5 unit atau kurang per tahun) adalah pilihan saya.** Batas
  yang berbeda akan menghasilkan jumlah SKU dan nilai yang berbeda.

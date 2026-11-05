# Analisis dan Peramalan Volatilitas Saham BSE (Ambuja Cement & Suzlon)

Proyek ini membangun alur analisis volatilitas saham India (BSE) dari awal sampai peramalan: mengambil data harga harian, menyimpannya, menghitung return, mengukur volatilitas, lalu memprediksinya dengan model GARCH(1,1).

## Tujuan
- Membangun pipeline data saham yang rapi dan tervalidasi.
- Memahami karakter return dan volatilitas saham Ambuja Cement (AMBUJACEM.BSE) dan Suzlon (SUZLON.BSE).
- Meramalkan volatilitas harian Ambuja Cement.

## Alur Proyek

| Tahap | Isi |
|---|---|
| 1. Pengambilan & eksplorasi data | Data harian dari Alpha Vantage (API ditiru dengan `mock_alpha`) diubah menjadi DataFrame bertipe waktu dan disimpan ke CSV. Dihitung log return, statistik ringkas, skewness, kurtosis, dan rolling volatility 21 hari. |
| 2. Pipeline data modular | Dua kelas buatan sendiri: `AlphaVantageAPI` (mengambil data) dan `SQLRepository` (menyimpan dan membaca data dari SQLite). Harga dan return kedua saham dibandingkan. |
| 3. Pemodelan volatilitas | Volatilitas harian dan tahunan, rolling volatility 50 hari, ACF/PACF return kuadrat, model GARCH(1,1) (library `arch`), walk-forward validation, dan prediksi volatilitas 10 hari ke depan. |

## Teknologi
Python, pandas, NumPy, matplotlib, statsmodels, arch, SQLite, requests.

## Temuan Utama
- Return rata-rata hampir nol, tetapi sebarannya besar dan distribusinya berekor tebal (excess kurtosis Ambuja sangat tinggi).
- Volatilitas tidak konstan dan mengelompok (*volatility clustering*), sehingga GARCH layak digunakan.
- Suzlon lebih berisiko: volatilitas tahunan sekitar 57,4% vs sekitar 31,3% untuk Ambuja.
- GARCH(1,1) dilatih pada 2.000 observasi (AIC 8169,74; BIC 8192,14). Prediksi volatilitas harian 10 hari ke depan berkisar 1,82% sampai 1,90%.

## Validasi
Setiap tahap dijaga `assert` dan checkpoint (tipe data, indeks tanggal, nama kolom, tanpa NaN, panjang data). Model dievaluasi dengan walk-forward validation (500 kali pelatihan ulang, prediksi 1 hari ke depan).

## Keterbatasan dan Langkah Lanjut
- Terdapat return ekstrem (sekitar -203% pada log return) yang kemungkinan berasal dari corporate action atau data yang belum disesuaikan. Perlu diperiksa, sebaiknya dengan adjusted close.
- Pada notebook 2, `read_table(limit=2500)` hanya mengambil 2.500 baris pertama (periode awal), bukan data terbaru.
- Model memakai distribusi Normal. Distribusi Student-t bisa dicoba untuk ekor tebal.
- Evaluasi masih visual. Tambahkan metrik kuantitatif seperti RMSE atau uji cakupan pita volatilitas.

## Cara Menjalankan
1. Pasang dependensi: `pip install pandas numpy matplotlib statsmodels arch requests`.
2. Pastikan modul `mock_alpha` dan `data` (berisi `AlphaVantageAPI` dan `SQLRepository`) ada di folder proyek.
3. Jalankan notebook secara berurutan sesuai tahap di atas.

# 📊 Management Dashboard Streamlit

Aplikasi dashboard berbasis web yang dibangun dengan **Streamlit** untuk memproses dan memvisualisasikan data transaksi keuangan (Fixed Income, Money Market, Spot, dan Swap) langsung dari Google Sheets.

## 🚀 Fitur Utama
- **Auto-Sync Google Drive**: Menarik data secara otomatis dari Google Sheets menggunakan Service Account.
- **Login System**: Keamanan akses menggunakan kredensial yang tersimpan di Streamlit Secrets.
- **Filtering Data**: Filter berdasarkan rentang tanggal yang dinamis.
- **Visualisasi Interaktif**: Grafik bar horizontal menggunakan Plotly dengan opsi pengurutan (Ascending/Descending).
- **FX Combined View**: Fitur untuk menggabungkan data kategori 'Spot' dan 'Swap' menjadi satu tampilan 'FX Total'.
- **Data Explorer**: Tabel mentah untuk meninjau data yang telah diproses.

## 🛠️ Tech Stack

Proyek ini dibangun menggunakan teknologi berikut:
* **Python**: Bahasa pemrograman utama.
* **Streamlit**: Framework untuk antarmuka dashboard web yang interaktif.
* **Pandas**: Digunakan untuk pembersihan, manipulasi, dan analisis data tabel.
* **Plotly Express**: Library untuk visualisasi data berupa grafik bar yang dinamis.
* **Gspread & Google OAuth**: Untuk autentikasi dan komunikasi dengan Google Sheets API.
* **Google Sheets**: Berperan sebagai database cloud untuk penyimpanan data transaksi.

---

## 📂 File Structure

Struktur folder proyek ini dirancang agar modular dan mudah dikelola:

```text
├── .streamlit/
│   └── secrets.toml       # Kredensial login & GCP Service Account (Local only)
├── app.py                 # File utama: Logika UI, Login, dan Filter Periode
├── data_processor.py      # Modul: Pengolahan data, cleaning, dan API Google Sheets
├── visualizer.py          # Modul: Logika pembuatan grafik Plotly
├── requirements.txt       # Daftar library Python yang dibutuhkan
├── .gitignore             # Daftar file yang tidak boleh diunggah (secrets.toml)
└── README.md              # Dokumentasi proyek
```

---

## 🛠️ Instalasi

1. **Clone Repositori**:
   ```bash
   git clone https://github.com/rexibernardino/Management-Dashboard

2. **Install Library**:
   ```bash
   pip install -r requirements.txt


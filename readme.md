# 📊 Management Dashboard Streamlit

Aplikasi dashboard berbasis web yang dibangun dengan **Streamlit** untuk memproses dan memvisualisasikan data transaksi keuangan (Fixed Income, Money Market, Spot, dan Swap) langsung dari Google Sheets.

## 🚀 Fitur Utama
- **Auto-Sync Google Drive**: Menarik data secara otomatis dari Google Sheets menggunakan Service Account.
- **Login System**: Keamanan akses menggunakan kredensial yang tersimpan di Streamlit Secrets.
- **Filtering Data**: Filter berdasarkan rentang tanggal yang dinamis.
- **Visualisasi Interaktif**: Grafik bar horizontal menggunakan Plotly dengan opsi pengurutan (Ascending/Descending).
- **FX Combined View**: Fitur untuk menggabungkan data kategori 'Spot' dan 'Swap' menjadi satu tampilan 'FX Total'.
- **Data Explorer**: Tabel mentah untuk meninjau data yang telah diproses.

## 🛠️ Instalasi

1. **Clone Repositori**:
   ```bash
   git clone [https://github.com/username/nama-repo.git](https://github.com/username/nama-repo.git)
   cd nama-repo

2. **Install Library**:
   ```bash
   pip install -r requirements.txt


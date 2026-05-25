import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import math


def clean_volume(val):
    if isinstance(val, (int, float)):
        return float(val)
    
    res = str(val).strip().replace('\xa0', '') # Hapus spasi kosong
    if not res or res == '-': return 0.0
    
    # Deteksi otomatis format ribuan
    # Jika ada koma dan titik, kita asumsikan karakter terakhir adalah desimal
    if ',' in res and '.' in res:
        if res.find('.') < res.find(','): # Format Indo: 1.234,56
            res = res.replace('.', '').replace(',', '.')
        else: # Format US: 1,234.56
            res = res.replace(',', '')
    elif ',' in res:
        # Jika hanya ada koma, cek apakah itu desimal atau ribuan
        # Seringkali di GSheets Indo, koma adalah desimal
        if len(res.split(',')[-1]) <= 2: # Contoh: 154,72 (desimal)
            res = res.replace(',', '.')
        else: # Contoh: 154,724 (ribuan)
            res = res.replace(',', '')
    elif '.' in res:
        # Jika hanya ada titik, cek apakah ribuan atau desimal
        if len(res.split('.')[-1]) > 2: # Contoh: 154.724 (ribuan)
            res = res.replace('.', '')
            
    try:
        return float(res)
    except:
        return 0.0
    
def parse_management_csv(file, date_selected):
    """Membaca CSV dengan format 4 kategori baru"""
    df_raw = pd.read_csv(file, sep=';', header=None)
    all_data = []
    
    # Mapping berdasarkan struktur baru Anda:
    # [StartRow, [Col_Name, Col_Vol], CategoryName, Unit]
    configs = [
        [3, [0, 4], 'Fixed Income', 'IDR BIO'],
        [3, [7, 11], 'Money Market', 'IDR BIO'],
        [3, [14, 18], 'Spot', 'USD MIO'],
        [3, [21, 25], 'Swap', 'USD MIO']
    ]
    
    for start_row, cols, cat_name, unit in configs:
        temp = df_raw.iloc[start_row:, cols].dropna()
        temp.columns = ['Broker_Name', 'Volume']
        temp = temp[~temp['Broker_Name'].str.contains('Total', case=False, na=False)]
        temp['Category'] = cat_name
        temp['Unit'] = unit
        all_data.append(temp)
    
    final_df = pd.concat(all_data, ignore_index=True)
    final_df['Volume'] = final_df['Volume'].apply(clean_volume)
    final_df['Date'] = pd.to_datetime(date_selected).date()
    return final_df

def calculate_ranking(df, category, target_col='Volume'):
    if df.empty:
        return pd.DataFrame(columns=['Rank', 'Broker_Name', target_col, 'Percentage (%)'])
    
    filtered_df = df[df['Category'] == category].copy()
    
    # --- PERBAIKAN: Normalisasi Nama Broker ---
    filtered_df['Broker_Name'] = filtered_df['Broker_Name'].str.strip()
    
    filtered_df[target_col] = pd.to_numeric(filtered_df[target_col], errors='coerce').fillna(0)
    
    # Grouping dan Sum
    ranked = filtered_df.groupby('Broker_Name')[target_col].sum().reset_index()
    
    # --- PERBAIKAN: Pastikan hasil sum tetap di-trunc agar tidak ada akumulasi desimal ---
    ranked[target_col] = ranked[target_col].apply(lambda x: float(math.trunc(x)))
    
    ranked = ranked.sort_values(by=target_col, ascending=False).reset_index(drop=True)
    
    total_value = ranked[target_col].sum()
    ranked['Percentage (%)'] = (ranked[target_col] / total_value * 100) if total_value > 0 else 0
    
    ranked.index += 1
    ranked.index.name = 'Rank'
    return ranked.reset_index()

def load_data_from_gdrive(spreadsheet_url):
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(spreadsheet_url)
        
        all_data_frames = []
        
        # Iterasi ke semua sheet (Januari, Februari, dst.)
        for worksheet in sheet.worksheets():
            data_raw = worksheet.get_all_values()
            if not data_raw or len(data_raw) < 4: continue
            
            df_raw = pd.DataFrame(data_raw)
            
            # Mapping Kolom sesuai struktur Anda:
            # Fixed Income (A-F), Money Market (H-M), Spot (O-T), Swap (V-AA)
            # Kolom Date berada pada indeks 3, 10, 17, dan 24
            configs = [
                # Format: [BarisMulai, [IndeksBroker, IndeksDate, IndeksVol, IndeksFee], NamaKategori]
                [3, [0,2 , 3, 4, 5], 'Fixed Income'],   # Broker(A),Bank(C), Date(D), Volume(E), Fee(F)
                [3, [7, 9,10, 11, 12], 'Money Market'], # Broker(H),Bank(K), Date(L), Volume(M), Fee(N)
                [3, [14, 16,17, 18, 19], 'Spot'],        # Broker(O),Bank(R), Date(S), Volume(T), Fee(U)
                [3, [21, 23,24, 25, 26], 'Swap']         # Broker(V),Bank(Y), Date(Z), Volume(AA), Fee(AB)
            ]
            
            for start_row, cols, cat_name in configs:
                try:
                    temp = df_raw.iloc[start_row:, cols].copy()
                    temp.columns = ['Broker_Name', 'Bank', 'Date', 'Volume', 'Fee']
                    
                    # Bersihkan baris kosong dan total
                    temp = temp[temp['Broker_Name'] != ""]
                    temp = temp[~temp['Broker_Name'].str.contains('Total|Name', case=False, na=False)]
                    
                    # Ubah kolom Date menjadi tipe datetime agar bisa difilter
                    temp['Date'] = pd.to_datetime(temp['Date'], dayfirst=True, errors='coerce')
                    temp['Volume'] = temp['Volume'].apply(clean_volume)
                    temp['Fee'] = temp['Fee'].apply(clean_volume)
                    temp['Category'] = cat_name
                    
                    all_data_frames.append(temp.dropna(subset=['Date']))
                except:
                    continue

        if not all_data_frames:
            return pd.DataFrame(), sheet.title

        final_df = pd.concat(all_data_frames, ignore_index=True)
        return final_df, sheet.title
        
    except Exception as e:
        raise Exception(f"Gagal akses Google Drive: {str(e)}")
    
def load_data_automatically():
    """Menarik data terbaru dari GDrive menggunakan URL di st.secrets"""
    try:
        url = st.secrets["config"]["spreadsheet_url"]
        return load_data_from_gdrive(url)
    except Exception as e:
        st.error(f"Gagal Sinkronisasi Otomatis: {e}")
        return pd.DataFrame(), "Dashboard"

def calculate_bank_ranking(df_filtered, selected_categories, group_by_bank=False, target_col='Volume'):
    """
    Menghitung akumulasi nilai (Volume/Fee) per Bank berdasarkan filter divisi yang dipilih.
    """
    if df_filtered.empty:
        return pd.DataFrame(columns=['Bank', target_col])
    
    df_to_process = df_filtered.copy()
    
    # Filter berdasarkan kategori divisi yang dipilih
    if "Semua Divisi" not in selected_categories and selected_categories:
        df_to_process = df_to_process[df_to_process['Category'].isin(selected_categories)]
        
    if df_to_process.empty:
        return pd.DataFrame(columns=['Bank', target_col])
        
    df_to_process['Bank'] = df_to_process['Bank'].fillna('Unknown').str.strip()
    df_to_process[target_col] = pd.to_numeric(df_to_process[target_col], errors='coerce').fillna(0)
    
    # Grouping berdasarkan Bank
    ranked_bank = df_to_process.groupby('Bank')[target_col].sum().reset_index()
    
    # Truncate nilai desimal agar konsisten dengan visualisasi volume/fee sebelumnya
    ranked_bank[target_col] = ranked_bank[target_col].apply(lambda x: float(math.trunc(x)))
    
    # Default sort descending (terbesar ke terkecil) untuk keperluan plotting awal
    ranked_bank = ranked_bank.sort_values(by=target_col, ascending=False).reset_index(drop=True)
    
    # Menyesuaikan nama kolom output agar fungsi visualizer.py (create_bar_chart) 
    # bisa membaca sumbu Y dengan mengganti nama kolom Bank menjadi Broker_Name secara temporer
    ranked_bank = ranked_bank.rename(columns={'Bank': 'Broker_Name'})
    
    return ranked_bank

def parse_sheet_to_dataframe(worksheet):
    data_raw = worksheet.get_all_values()
    if not data_raw: return pd.DataFrame()
    
    df_raw = pd.DataFrame(data_raw)
    all_data = []
    
    # Mapping berdasarkan struktur kolom Anda:
    # FIXED INCOME (Kolom A-F, Date di D) | MONEY MARKET (Kolom H-M, Date di K) ...
    configs = [
            [3, [0, 2,3, 4, 5], 'Fixed Income'],
            [3, [7, 9,10, 11, 12], 'Money Market'],
            [3, [14, 16,17, 18, 19], 'Spot'],
            [3, [21, 23,24, 25, 26], 'Swap']
        ]
    
    for start_row, cols, cat_name in configs:
        try:
            temp = df_raw.iloc[start_row:, cols].copy()
            temp.columns = ['Broker_Name', 'Bank', 'Date', 'Volume', 'Fee']
            
            # Bersihkan data kosong
            temp = temp[temp['Broker_Name'] != ""]
            temp = temp[~temp['Broker_Name'].str.contains('Total|Name', case=False, na=False)]
            
            # Konversi kolom Date ke datetime agar bisa difilter di app.py
            temp['Date'] = pd.to_datetime(temp['Date'], errors='coerce')
            temp = temp.dropna(subset=['Date']) # Buang jika tanggal tidak valid
            
            temp['Category'] = cat_name
            all_data.append(temp)
        except Exception:
            continue
            
    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

def calculate_ranking_combined(df_subset, target_col='Volume'):
    if df_subset.empty:
        return pd.DataFrame(columns=['Rank', 'Broker_Name', target_col, 'Percentage (%)'])
    
    # Normalisasi Nama
    df_subset = df_subset.copy()
    df_subset['Broker_Name'] = df_subset['Broker_Name'].str.strip()
    
    # Grouping
    ranked = df_subset.groupby('Broker_Name')[target_col].sum().reset_index()
    
    # --- PERBAIKAN: Gunakan Truncation, Bukan Round ---
    ranked[target_col] = ranked[target_col].apply(lambda x: float(math.trunc(x)))
    
    ranked = ranked.sort_values(by=target_col, ascending=False).reset_index(drop=True)
    
    total_value = ranked[target_col].sum()
    # Hapus .round(2) di sini untuk konsistensi murni
    ranked['Percentage (%)'] = (ranked[target_col] / total_value * 100) if total_value > 0 else 0
    
    ranked.index += 1
    ranked.index.name = 'Rank'
    return ranked.reset_index()
    """
    Menghitung ranking dari dataframe yang sudah difilter sebelumnya (misal: gabungan Spot & Swap).
    Konsisten dengan calculate_ranking() dalam hal kolom yang digunakan.
    """
    if df_subset.empty:
        return pd.DataFrame(columns=['Rank', 'Broker_Name', target_col, 'Percentage (%)'])
    
    # Kelompokkan berdasarkan Broker dan jumlahkan nilai target_col
    ranked = df_subset.groupby('Broker_Name')[target_col].sum().reset_index()
    ranked[target_col] = ranked[target_col].round(2)
    
    # Sort berdasarkan target_col (akan di-override oleh sorting di visualizer)
    ranked = ranked.sort_values(by=target_col, ascending=False).reset_index(drop=True)
    
    # Hitung persentase
    total_value = ranked[target_col].sum()
    ranked['Percentage (%)'] = (ranked[target_col] / total_value * 100).round(2) if total_value > 0 else 0
    
    # Tambahkan rank
    ranked.index += 1
    ranked.index.name = 'Rank'
    return ranked.reset_index()

def calculate_monthly_recap(df_filtered):
    if df_filtered.empty:
        return pd.DataFrame()

    df = df_filtered.copy()
    
    df['Bank'] = df['Bank'].fillna('Unknown')
    df['Broker_Name'] = df['Broker_Name'].fillna('Unknown')
    
    # --- PERBAIKAN: Sertakan Tahun dalam Nama Bulan ---
    # Gunakan format '%b %Y' untuk menghasilkan 'Jan 2024'
    df['Month_Year'] = df['Date'].dt.strftime('%b %Y') 
    
    # Karena urutan bulan sekarang dinamis (tergantung tahun), 
    # kita urutkan berdasarkan tanggal aslinya agar kolom tidak berantakan
    df = df.sort_values('Date')
    sorted_months = df['Month_Year'].unique()
    
    # Pivot Table
    pivot = df.pivot_table(
        index=['Bank', 'Broker_Name'],
        columns='Month_Year', # Gunakan kolom baru
        values='Fee',
        aggfunc='sum'
    ).fillna(0)

    # Reindex agar urutan kolom sesuai urutan waktu (Jan 24, Feb 24, dst)
    pivot = pivot.reindex(columns=sorted_months)

    pivot['Total'] = pivot.sum(axis=1)
    pivot['Average'] = pivot[sorted_months].mean(axis=1)

    return pivot
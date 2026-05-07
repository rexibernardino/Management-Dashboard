import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st


def clean_volume(val):
    try:
        # Jika sudah angka, langsung kembalikan float
        if isinstance(val, (int, float)):
            return float(val)
        # Jika string, bersihkan karakter aneh tapi jaga titik desimal
        # Hapus spasi atau karakter non-numerik kecuali titik/koma
        res = str(val).strip()
        # Jika locale Indonesia (koma adalah desimal), ganti koma ke titik
        if ',' in res and '.' in res: # Kasus 1.234,56
            res = res.replace('.', '').replace(',', '.')
        elif ',' in res: # Kasus 1234,56
            res = res.replace(',', '.')
            
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
    ranked = filtered_df.groupby('Broker_Name')[target_col].sum().reset_index()
    ranked[target_col] = ranked[target_col].round(2)
    ranked = ranked.sort_values(by=target_col, ascending=False).reset_index(drop=True)
    
    total_volume = ranked[target_col].sum()
    ranked['Percentage (%)'] = (ranked[target_col] / total_volume * 100).round(2) if total_volume > 0 else 0
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
                    [3, [0, 3, 4, 5], 'Fixed Income'], # Fee di indeks 5
                    [3, [7, 10, 11, 12], 'Money Market'], # Fee di indeks 12
                    [3, [14, 17, 18, 19], 'Spot'], # Fee di indeks 19
                    [3, [21, 24, 25, 26], 'Swap'] # Fee di indeks 26
                ]
            
            for start_row, cols, cat_name in configs:
                try:
                    temp = df_raw.iloc[start_row:, cols].copy()
                    temp.columns = ['Broker_Name', 'Date', 'Volume', 'Fee']
                    
                    # Bersihkan baris kosong dan total[cite: 2]
                    temp = temp[temp['Broker_Name'] != ""]
                    temp = temp[~temp['Broker_Name'].str.contains('Total|Name', case=False, na=False)]
                    
                    # Ubah kolom Date menjadi tipe datetime agar bisa difilter[cite: 2]
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
    
def parse_sheet_to_dataframe(worksheet):
    data_raw = worksheet.get_all_values()
    if not data_raw: return pd.DataFrame()
    
    df_raw = pd.DataFrame(data_raw)
    all_data = []
    
    # Mapping berdasarkan struktur kolom Anda:
    # FIXED INCOME (Kolom A-F, Date di D) | MONEY MARKET (Kolom H-M, Date di K) ...
    configs = [
        [2, [0, 3, 4, 5], 'Fixed Income'], # Nama Broker (A), Date (D), Volume (E), Fee (F)
        [2, [7, 10, 11, 12], 'Money Market'], # Nama Broker (H), Date (K), Volume (L), Fee (M)
        [2, [14, 17, 18, 19], 'Spot'],        # Nama Broker (O), Date (R), Volume (S), Fee (T)
        [2, [21, 24, 25, 26], 'Swap']         # Nama Broker (V), Date (Y), Volume (Z), Fee (AA)
    ]
    
    for start_row, cols, cat_name in configs:
        try:
            temp = df_raw.iloc[start_row:, cols].copy()
            temp.columns = ['Broker_Name', 'Date', 'Volume', 'Fee']
            
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

# --- Tambahkan di data_processor.py ---
def calculate_ranking_combined(df_subset, target_col='Volume'):
    """
    Menghitung ranking dari dataframe yang sudah difilter sebelumnya (misal: gabungan Spot & Swap)
    """
    if df_subset.empty:
        return pd.DataFrame(columns=['Rank', 'Broker_Name', target_col, 'Percentage (%)'])
    
    # Kelompokkan berdasarkan Broker dan jumlahkan volumenya
    ranked = df_subset.groupby('Broker_Name')[[target_col, 'Fee']].sum().reset_index()
    ranked = ranked.sort_values(by=target_col, ascending=False).reset_index(drop=True)
    
    total_volume = ranked[target_col].sum()
    ranked['Percentage (%)'] = (ranked[target_col] / total_volume * 100).round(2) if total_volume > 0 else 0
    ranked.index += 1
    ranked.index.name = 'Rank'
    return ranked.reset_index()
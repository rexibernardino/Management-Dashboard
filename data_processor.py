import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st


def clean_volume(val):
    if pd.isna(val) or val == "":
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    res = str(val).replace('.', '').replace(',', '.')
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

def calculate_ranking(df, category):
    if df.empty:
        return pd.DataFrame(columns=['Rank', 'Broker_Name', 'Volume', 'Percentage (%)'])
    
    filtered_df = df[df['Category'] == category].copy()
    ranked = filtered_df.groupby('Broker_Name')['Volume'].sum().reset_index()
    ranked = ranked.sort_values(by='Volume', ascending=False).reset_index(drop=True)
    
    total_volume = ranked['Volume'].sum()
    ranked['Percentage (%)'] = (ranked['Volume'] / total_volume * 100).round(2) if total_volume > 0 else 0
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
                [3, [0, 3, 4], 'Fixed Income'], # Broker Name (0), Date (3), Volume (4)
                [3, [7, 10, 11], 'Money Market'],
                [3, [14, 17, 18], 'Spot'],
                [3, [21, 24, 25], 'Swap']
            ]
            
            for start_row, cols, cat_name in configs:
                try:
                    temp = df_raw.iloc[start_row:, cols].copy()
                    temp.columns = ['Broker_Name', 'Date', 'Volume']
                    
                    # Bersihkan baris kosong dan total[cite: 2]
                    temp = temp[temp['Broker_Name'] != ""]
                    temp = temp[~temp['Broker_Name'].str.contains('Total|Name', case=False, na=False)]
                    
                    # Ubah kolom Date menjadi tipe datetime agar bisa difilter[cite: 2]
                    temp['Date'] = pd.to_datetime(temp['Date'], dayfirst=True, errors='coerce')
                    temp['Volume'] = temp['Volume'].apply(clean_volume)
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
        [2, [0, 3, 4], 'Fixed Income'], # Nama Broker (A), Date (D), Volume (E)
        [2, [7, 10, 11], 'Money Market'], # Nama Broker (H), Date (K), Volume (L)
        [2, [14, 17, 18], 'Spot'],        # Nama Broker (O), Date (R), Volume (S)
        [2, [21, 24, 25], 'Swap']         # Nama Broker (V), Date (Y), Volume (Z)
    ]
    
    for start_row, cols, cat_name in configs:
        try:
            temp = df_raw.iloc[start_row:, cols].copy()
            temp.columns = ['Broker_Name', 'Date', 'Volume']
            
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
def calculate_ranking_combined(df_subset):
    """
    Menghitung ranking dari dataframe yang sudah difilter sebelumnya (misal: gabungan Spot & Swap)
    """
    if df_subset.empty:
        return pd.DataFrame(columns=['Rank', 'Broker_Name', 'Volume', 'Percentage (%)'])
    
    # Kelompokkan berdasarkan Broker dan jumlahkan volumenya
    ranked = df_subset.groupby('Broker_Name')['Volume'].sum().reset_index()
    ranked = ranked.sort_values(by='Volume', ascending=False).reset_index(drop=True)
    
    total_volume = ranked['Volume'].sum()
    ranked['Percentage (%)'] = (ranked['Volume'] / total_volume * 100).round(2) if total_volume > 0 else 0
    ranked.index += 1
    ranked.index.name = 'Rank'
    return ranked.reset_index()
import streamlit as st
import pandas as pd
from data_processor import load_data_automatically, calculate_ranking, calculate_ranking_combined
from visualizer import create_bar_chart

st.set_page_config(page_title="Management Dashboard",page_icon="📋", layout="wide")

# --- FUNGSI LOGIN ---
def check_password():
    def login_form():
        with st.form("login"):
            st.subheader("🔐 Login Required")
            
            # Mendefinisikan variabel input
            user_input = st.text_input("Username") 
            pw_input = st.text_input("Password", type="password")
            
            if st.form_submit_button("Log In"):
                try:
                    # Mengambil data dari secrets.toml
                    allowed_users = st.secrets["auth"]["username"] 
                    allowed_passwords = st.secrets["auth"]["password"]
                    
                    if user_input in allowed_users:
                        user_index = allowed_users.index(user_input)
                        if pw_input == allowed_passwords[user_index]:
                            st.session_state["authenticated"] = True
                            st.session_state["username"] = user_input
                            st.rerun()
                        else:
                            st.error("Password salah")
                    else:
                        st.error("Username tidak terdaftar")
                except KeyError:
                    st.error("Konfigurasi [auth] tidak ditemukan di secrets.toml")

    if "authenticated" not in st.session_state:
        login_form()
        return False
    return True


# --- LOGIK JALANKAN APLIKASI ---


if check_password():
    st.sidebar.title(f"👋 Halo, {st.session_state.get('username', 'Admin')}")
        
        # --- SIDEBAR & NAVIGASI ---
    col_side1, col_side2 = st.sidebar.columns(2)
    with col_side1:
        if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            del st.session_state.main_df
            st.rerun()
        
    with col_side2:
        if st.sidebar.button("🚪 Logout",use_container_width=True):
            del st.session_state.authenticated
            st.rerun()

    st.sidebar.divider()
    # --- SIDEBAR MENU ---
    menu = st.sidebar.radio("Menu", ["Dashboard by Volume", "Dashboard by Fee", "Data Explorer"])
    categories = ["Fixed Income", "Money Market", "Spot", "Swap"]

    if 'main_df' not in st.session_state:
        with st.spinner("Menarik data terbaru..."):
            df, title = load_data_automatically()
            st.session_state.main_df = df
            st.session_state.sheet_title = title

    if menu in ["Dashboard by Volume", "Dashboard by Fee"]:
        active_metric = "Volume" if menu == "Dashboard by Volume" else "Fee"

        st.title(f"📊 {st.session_state.sheet_title} ({active_metric})")
            
        date_range = [] 
        st.sidebar.divider()

        if not st.session_state.main_df.empty:
                # Memastikan kolom Date adalah format datetime
            st.session_state.main_df['Date'] = pd.to_datetime(st.session_state.main_df['Date'])
                
            min_date = st.session_state.main_df['Date'].min().date()
            max_date = st.session_state.main_df['Date'].max().date()

            st.sidebar.subheader("📅 Filter Periode")
                
                # Mendefinisikan date_range melalui input user
            date_range = st.sidebar.date_input(
                    "Pilih Rentang Waktu",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                    help="Pilih tanggal mulai dan akhir untuk memfilter data transaksi."
                )

            # --- EKSEKUSI FILTER DATA ---
            # Membuat salinan data untuk difilter agar tidak merusak data asli
        df_filtered = st.session_state.main_df.copy()

            # Cek apakah date_range sudah berisi tuple tanggal (mulai, akhir)[cite: 1]
        if isinstance(date_range, tuple) and len(date_range) == 2:
                start_date, end_date = date_range
                # Filter data berdasarkan kolom Date[cite: 1, 2]
                mask = (df_filtered['Date'].dt.date >= start_date) & (df_filtered['Date'].dt.date <= end_date)
                df_filtered = df_filtered.loc[mask]
                date_info = f"({start_date} - {end_date})"
                st.info(f"📍 Menampilkan data **{active_metric}** dari **{start_date}** sampai **{end_date}**")

        else:
                # Jika user baru klik tanggal mulai saja, tampilkan pesan instruksi[cite: 1]
            st.warning("Silakan pilih tanggal akhir pada kalender untuk melengkapi rentang waktu.")
            df_filtered = pd.DataFrame()

            # Konfigurasi Unit Mata Uang per Kategori
        unit_mapping = {
                "Fixed Income": "IDR BIO",
                "Money Market": "IDR BIO",
                "Spot": "USD MIO",
                "Swap": "USD MIO",
                "FX Combined": "USD MIO"
                }

        sort_choice = st.sidebar.selectbox(f"Urutan {active_metric}:", ["Terbesar (Descending)", "Terkecil (Ascending)"], )
        is_asc = True if sort_choice == "Terkecil (Ascending)" else False

        view_option = st.sidebar.radio("Tampilan FX (Spot & Swap):",["Dipisah", "Digabung (FX Total)"])

        if view_option == "Dipisah":
            display_categories = ["Fixed Income", "Money Market", "Spot", "Swap"]
        else:
            display_categories = ["Fixed Income", "Money Market", "FX Combined"]
        
        cols = st.columns(2)

        for i, cat in enumerate(display_categories):
            with cols[i % 2]:
                unit = unit_mapping.get(cat, "")
                st.markdown(f"#### {cat} ({unit})")
                    
                if cat == "FX Combined":
                    # LOGIKA GABUNGAN: Filter data yang kategorinya Spot ATAU Swap[cite: 1, 2]
                    df_fx = df_filtered[df_filtered['Category'].isin(['Spot', 'Swap'])]
                    
                    # Hitung ranking dari hasil gabungan tersebut
                    df_cat = df_fx.groupby('Broker_Name')[active_metric].sum().reset_index()
                    df_cat = df_cat.sort_values(by=active_metric, ascending=False).reset_index(drop=True)
                    total_val = df_cat[active_metric].sum()
                    df_cat['Percentage (%)'] = (df_cat[active_metric] / total_val * 100).round(2) if total_val > 0 else 0
                    df_cat.index += 1
                    df_cat = df_cat.reset_index().rename(columns={'index': 'Rank'})
                else:
                    # LOGIKA TERPISAH: Jalankan fungsi normal untuk kategori tunggal[cite: 1, 2]
                    df_cat = calculate_ranking(df_filtered, cat, target_col=active_metric) 
                    
                if not df_cat.empty:
                    color_theme = "Viridis" if active_metric == "Volume" else "Plasma"
                    # Render chart[cite: 3]
                    fig = create_bar_chart(df_cat, f"Contribution {cat} {date_info}", color_theme, is_ascending=is_asc, target_val=active_metric)
                    # Gunakan key yang unik agar Streamlit tidak konflik saat berpindah mode[cite: 1]
                    st.plotly_chart(fig, use_container_width=True, key=f"chart_{cat}_{menu}_{view_option}_{date_range}")
                else:
                    st.caption(f"⚠️ Tidak ada transaksi {cat} di rentang ini.")
                    
    if menu == "Data Explorer":
        st.title("🗂️ Data Explorer")
        st.dataframe(
            st.session_state.main_df, 
            column_config={
                "Volume": st.column_config.NumberColumn(format="%,.2f"),
                "Fee": st.column_config.NumberColumn(format="%,.2f"),
            },
            use_container_width=True
        )

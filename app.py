import streamlit as st
import pandas as pd
from data_processor import (
    load_data_automatically, 
    calculate_ranking, 
    calculate_ranking_combined,
    calculate_monthly_recap 
    )
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
    menu = st.sidebar.radio("Menu", ["Dashboard by Volume", "Dashboard by Fee", "Dashboard by Bank & Broker", "Data Explorer"])
    categories = ["Fixed Income", "Money Market", "Spot", "Swap"]

    if 'main_df' not in st.session_state:
        with st.spinner("Menarik data terbaru..."):
            df, title = load_data_automatically()
            st.session_state.main_df = df
            st.session_state.sheet_title = title

    active_metric = "Volume" if menu == "Dashboard by Volume" else "Fee" if menu == "Dashboard by Fee" else "Bank & Broker Recap" if menu == "Dashboard by Bank & Broker" else "Data Explorer"

    # --- PENYIAPAN DATA ---
    # Selalu gunakan copy() agar st.session_state.main_df tidak rusak
    df_working = st.session_state.main_df.copy()
    df_working['Date'] = pd.to_datetime(df_working['Date']) 
    # Inisialisasi date_range dengan nilai default dari data agar tidak kosong
    date_range = None

    if not df_working.empty:
        min_date = df_working['Date'].min().date()
        max_date = df_working['Date'].max().date()

        st.sidebar.subheader("📅 Filter Periode")
                
        # ✅ PERBAIKAN: Inisialisasi session_state untuk date_range jika belum ada
        if "selected_date_range" not in st.session_state:
            st.session_state.selected_date_range = (min_date, max_date)
                
        # ✅ PERBAIKAN: Gunakan key yang SAMA untuk semua menu, ambil nilai dari session_state
        date_range = st.sidebar.date_input(
            "Pilih Rentang Waktu",
            value=st.session_state.selected_date_range,
            min_value=min_date,
            max_value=max_date,
            key="global_date_range", # Key sama untuk semua menu
            help="Pilih tanggal mulai dan akhir untuk memfilter data transaksi."
            )
                
                # ✅ PERBAIKAN: Simpan pilihan user ke session_state
        if isinstance(date_range, tuple) and len(date_range) == 2:
            st.session_state.selected_date_range = date_range

        # --- EKSEKUSI FILTER ---
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            mask = (df_working['Date'].dt.date >= start_date) & (df_working['Date'].dt.date <= end_date)
            df_filtered = df_working.loc[mask].copy()
            date_info = f"({start_date} - {end_date})"
            st.info(f"📍 Menampilkan data **{active_metric}** dari **{start_date}** sampai **{end_date}**")
        else:
            st.warning("Silakan pilih tanggal akhir pada kalender untuk melengkapi rentang waktu.")
            df_filtered = pd.DataFrame()
            date_info = ""

    if menu in ["Dashboard by Volume", "Dashboard by Fee"]:

            st.title(f"📊 {st.session_state.sheet_title} ({active_metric})")

            st.sidebar.divider()

            # --- KONFIGURASI TAMPILAN ---
            unit_mapping = {
                "Fixed Income": "IDR BIO",
                "Money Market": "IDR BIO",
                "Spot": "USD MIO",
                "Swap": "USD MIO",
                "FX Combined": "USD MIO"
            }

            # ✅ PERBAIKAN: Inisialisasi session_state untuk sort_choice
            if "selected_sort" not in st.session_state:
                st.session_state.selected_sort = "Terbesar (Descending)"
            
            sort_choice = st.sidebar.selectbox(
                f"Urutan {active_metric}:", 
                ["Terbesar (Descending)", "Terkecil (Ascending)"], 
                index=0 if st.session_state.selected_sort == "Terbesar (Descending)" else 1,
                key="global_sort_choice"  # Key yang sama untuk semua menu
            )
            
            # ✅ PERBAIKAN: Simpan pilihan user
            st.session_state.selected_sort = sort_choice
            is_asc = True if sort_choice == "Terkecil (Ascending)" else False

            # ✅ PERBAIKAN: Inisialisasi session_state untuk view_option
            if "selected_view" not in st.session_state:
                st.session_state.selected_view = "Dipisah"
            
            view_option = st.sidebar.radio(
                "Tampilan FX (Spot & Swap):",
                ["Dipisah", "Digabung (FX Total)"],
                index=0 if st.session_state.selected_view == "Dipisah" else 1,
                key="global_view_option"  # Key yang sama untuk semua menu
            )
            
            # ✅ PERBAIKAN: Simpan pilihan user
            st.session_state.selected_view = view_option

            display_categories = ["Fixed Income", "Money Market", "Spot", "Swap"] if view_option == "Dipisah" else ["Fixed Income", "Money Market", "FX Combined"]
            
            cols = st.columns(2)

            # --- RENDER DASHBOARD ---
            for i, cat in enumerate(display_categories):
                with cols[i % 2]:
                    # Gunakan unit dari mapping, jika Fee mungkin Anda ingin menggantinya ke IDR 
                    if active_metric == "Fee":
                     # Jika sedang di Dashboard Fee, gunakan format (in Rupiah)
                        unit = "in Rupiah"
                    else:
                        # Jika di Dashboard Volume, gunakan mapping IDR BIO / USD MIO
                        unit = unit_mapping.get(cat, "")
                    st.markdown(f"#### {cat} ({unit})")
                        
                    if cat == "FX Combined":
                        # LOGIKA GABUNGAN: Filter data Spot & Swap dari df_filtered yang sudah bersih
                        df_fx = df_filtered[df_filtered['Category'].isin(['Spot', 'Swap'])]
                        
                        if not df_fx.empty:
                            # PERBAIKAN: Gunakan calculate_ranking_combined dengan target_col yang sesuai
                            df_cat = calculate_ranking_combined(df_fx, target_col=active_metric)
                        else:
                            df_cat = pd.DataFrame()
                    else:
                        # LOGIKA TERPISAH: Gunakan calculate_ranking dengan target_col yang sesuai
                        df_cat = calculate_ranking(df_filtered, cat, target_col=active_metric) 
                        
                    if not df_cat.empty:
                        color_theme = "Viridis" if active_metric == "Volume" else "Plasma"
                        fig = create_bar_chart(
                            df_cat, 
                            f"{cat} {date_info}", 
                            color_theme, 
                            is_ascending=is_asc, 
                            target_val=active_metric
                        )
                        # Key unik untuk plotly chart agar tidak terjadi tabrakan ID komponen
                        st.plotly_chart(fig, use_container_width=True, key=f"chart_{cat}_{active_metric}_{view_option}")
                    else:
                        st.caption(f"⚠️ Tidak ada transaksi {cat} di rentang ini.")

    elif menu == "Dashboard by Bank & Broker":
        if "selected_date_range" in st.session_state and len(st.session_state.selected_date_range) == 2:
            start_date, end_date = st.session_state.selected_date_range
            
            # --- Filter Divisi ---
            st.sidebar.divider()
            st.sidebar.subheader("🎯 Filter Kategori")
            list_divisi = ["Semua Divisi"] + categories 
            
            selected_divisi = st.sidebar.multiselect(
                "Pilih Divisi:",
                list_divisi,
                default="Semua Divisi",
                key="filter_divisi_recap"
            )

            group_by_bank = st.sidebar.toggle("Gabungkan Semua Broker per Bank", value=False)

            # 2. Filter data utama
            mask = (st.session_state.main_df['Date'].dt.date >= start_date) & \
                   (st.session_state.main_df['Date'].dt.date <= end_date)
            df_to_process = st.session_state.main_df.loc[mask].copy()

            if "Semua Divisi" not in selected_divisi:
                df_to_process = df_to_process[df_to_process['Category'].isin(selected_divisi)]
                st.info(f"Menampilkan data untuk divisi: **{', '.join(selected_divisi)}**")

            st.title("🏦 Monthly Bank & Broker Recap")

            if not df_to_process.empty:
                # --- STEP 1: Hitung Pivot (HANYA SEKALI) ---
                recap_pivot = calculate_monthly_recap(df_to_process)

                # --- STEP 2: Logika Gabung Bank ---
                if group_by_bank:
                    df_temp = recap_pivot.reset_index()
                    agg_dict = {col: 'sum' for col in df_temp.columns if col not in ['Bank', 'Broker_Name']}
                    agg_dict['Broker_Name'] = lambda x: ', '.join(x.unique())
                    
                    recap_pivot = df_temp.groupby('Bank').agg(agg_dict)
                    recap_pivot = recap_pivot.reset_index().set_index(['Bank', 'Broker_Name'])
                
                # --- STEP 3: Tambahkan Grand Total ---
                grand_total = recap_pivot.sum(numeric_only=True).to_frame().T
                grand_total.index = pd.MultiIndex.from_tuples([('GRAND TOTAL', '')], names=['Bank', 'Broker_Name'])
                
                final_display = pd.concat([recap_pivot, grand_total])

                # --- STEP 4: Tampilkan Tabel ---
                month_cols = [c for c in recap_pivot.columns if c not in ['Total', 'Average']]
                st.dataframe(
                    final_display,
                    column_config={
                        **{m: st.column_config.NumberColumn(m, format="%,.0f") for m in month_cols},
                        "Total": st.column_config.NumberColumn("Total IDR", format="%,.0f", width="medium"),
                        "Average": st.column_config.NumberColumn("Avg IDR", format="%,.0f", width="medium"),
                    },
                    use_container_width=True
                )
                
                st.divider()
                m1, m2 = st.columns(2)
                m1.metric("Total Fee in Period", f"IDR {recap_pivot['Total'].sum():,.0f}")
                m2.metric("Bank Count", f"{df_to_process['Bank'].nunique()}")
                
            else:
                st.warning("Tidak ada data untuk rentang waktu yang dipilih.")
        else:
            st.error("Silakan tentukan rentang waktu terlebih dahulu di menu Dashboard.")
            

    elif menu == "Data Explorer":
        st.title("🗂️ Data Explorer")
        st.dataframe(
            st.session_state.main_df, 
            column_config={
                "Volume": st.column_config.NumberColumn(format="%,.2f"),
                "Fee": st.column_config.NumberColumn(format="%,.2f"),
            },
            use_container_width=True
        )
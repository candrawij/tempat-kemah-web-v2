import streamlit as st
import pandas as pd
import urllib.parse
import json
import os
import re
from src import utils
from src import mesin_pencari

# --- FUNGSI LOGGING (NONAKTIF SEMENTARA) ---
# ... (tetap nonaktif) ...

# ======================================================================
# 1. KONFIGURASI HALAMAN & CSS KUSTOM
# ======================================================================
st.set_page_config(
    page_title="Cari Kemah",
    page_icon="🏕️",
    layout="wide"
)

def load_css(file_name):
    """Memuat file CSS eksternal."""
    file_path = os.path.join(os.path.dirname(__file__), file_name)
    try:
        with open(file_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"File CSS '{file_name}' tidak ditemukan. Pastikan file ada di folder yang sama.")

# Panggil fungsi untuk memuat style.css
load_css("style.css")

# ======================================================================
# 2. INISIALISASI MESIN
# ======================================================================
@st.cache_resource
def muat_mesin_vsm():
    """Memuat semua aset VSM (Indeks, Kamus, Model) ke memori."""
    print("--- 🚀 MEMUAT ASET VSM... (Hanya berjalan sekali) ---")
    mesin_pencari.initialize_mesin() 
    print("--- ✅ ASET VSM SIAP ---")
    return True

muat_mesin_vsm()

# ======================================================================
# 3. PANEL ADMIN (SUDAH DIPERBARUI UNTUK G-SHEETS)
# ======================================================================

st.sidebar.title("Panel Admin")
admin_password = st.sidebar.text_input("Masukkan Password Admin", type="password")

admin_pass_rahasia = st.secrets.get("ADMIN_PASSWORD", "1234")

if admin_password == admin_pass_rahasia:
    st.sidebar.success("Mode Admin Aktif")
    st.sidebar.subheader("📊 Wawasan Pencarian")
    
    try:
        # 1. Panggil fungsi CSV
        # Baca 500 log terakhir untuk statistik yang baik
        df_log = utils.baca_riwayat_csv(limit=500) 
        
        if df_log.empty:
            st.sidebar.info("Belum ada riwayat pencarian.")
        else:
            st.sidebar.markdown("**Kueri Paling Populer:**")
            
            # 2. Hitung 5 kueri teratas
            top_queries = df_log['query_mentah'].value_counts().head(5)
            
            # 3. Tampilkan sebagai st.metric yang bersih
            for query, count in top_queries.items():
                st.sidebar.metric(label=f"'{query}'", value=f"{count} kali")
            
            # Tampilkan wawasan lain jika kolomnya ada
            if 'region' in df_log.columns:
                st.sidebar.markdown("**Region Paling Populer:**")
                # Filter 'None' atau string kosong
                top_regions = df_log[df_log['region'].notna() & (df_log['region'] != 'None')]['region'].value_counts().head(3)
                for region, count in top_regions.items():
                    st.sidebar.metric(label=f"'{region}'", value=f"{count} kali")

            with st.sidebar.expander("Tampilkan 50 Log Terakhir (Data Mentah)"):
                st.dataframe(df_log.head(50)) # Tampilkan 50 teratas di sini
            
    except Exception as e:
        st.sidebar.error(f"Gagal mengambil data log: {e}")

elif admin_password: # Jika password diisi tapi salah
    st.sidebar.error("Password admin salah.")

# ======================================================================
# TAMPILAN UTAMA
# ======================================================================

# Gunakan session state untuk menyimpan kueri
if 'query' not in st.session_state:
    st.session_state.query = ""
if 'search_performed' not in st.session_state:
    st.session_state.search_performed = False
if 'selected_item' not in st.session_state: # <-- State untuk st.dialog
    st.session_state.selected_item = None

st.title("🏕️ Cari Kemah")
st.markdown('<p class="sub-judul">Temukan tempat kemah ideal di Jawa Tengah & DIY</p>', unsafe_allow_html=True)
st.markdown('<p class="search-guide">Ketik misal: \'kamar mandi bersih\', \'sejuk di jogja\', \'terbaik di kendal\'</p>', unsafe_allow_html=True)
st.write("") # Spasi

col1, col_main, col3 = st.columns([1, 2, 1]) 
with col_main:
    with st.form(key="search_form"):
        query_input = st.text_input(
            "Cari tempat kemah...",
            placeholder="Ketik kata kunci di sini...",
            label_visibility="collapsed"
        )
        tombol_cari = st.form_submit_button(label="Cari")

# ======================================================================
# 5. LOGIKA & TAMPILAN HASIL (PERBAIKAN STATE MANAGEMENT)
# ======================================================================

# --- Inisialisasi state jika belum ada ---
if 'results_df' not in st.session_state:
    st.session_state.results_df = pd.DataFrame()
if 'query_info' not in st.session_state:
    st.session_state.query_info = {}

# --- 1. LOGIKA SAAT PENCARIAN BARU DILAKUKAN ---
if tombol_cari and query_input:
    st.session_state.search_performed = True
    st.session_state.modal_data = None # Tutup modal lama jika ada
    
    with st.spinner("⏳ Menganalisis ulasan dan mencari rekomendasi..."):
        vsm_tokens, intent, region = mesin_pencari.analyze_full_query(query_input)
        results = mesin_pencari.search_by_keyword(vsm_tokens, intent, region)

        utils.log_pencarian_csv(query_input, vsm_tokens, intent, region)
        
        # Simpan hasil ke session state agar tidak hilang saat rerun
        st.session_state.results_df = pd.DataFrame(results)
        
        # Simpan semua info kueri ke session state
        st.session_state.query_info = {
            "query": query_input,
            "tokens": vsm_tokens,
            "intent": intent,
            "region": region
        }

# --- 2. LOGIKA UNTUK MENAMPILKAN HASIL ---
# (Berjalan jika pencarian *pernah* dilakukan, terlepas dari tombol_cari)
if st.session_state.search_performed:
    st.divider()
    
    # Ambil data dari session state
    df_results = st.session_state.results_df
    info = st.session_state.query_info
    
    res_margin1, res_content, res_margin2 = st.columns([1, 3, 1])
    
    with res_content: 
        st.subheader(f"Hasil Pencarian untuk: '{info['query']}'")

        # Baca dari 'info' (session state), bukan dari variabel lokal
        st.caption(f"Token VSM: {info['tokens']} | Intent: {info['intent']} | Region: {info['region']}")

        st.write("") 

        if df_results.empty:
            st.warning("Maaf, tidak ditemukan tempat kemah yang cocok dengan kueri Anda.")
        else:
            grid_cols = st.columns(3) 
            
            for index, item_row in df_results.iterrows():

                item = item_row.to_dict()
                col = grid_cols[index % 3]
                
                with col:
                    with st.container(border=True):
                        # Tambahkan fallback untuk foto 'nan'
                        photo_url = item.get('photo_url')
                        if (not isinstance(photo_url, str) or 
                            pd.isna(photo_url) or 
                            not photo_url.startswith("http") or 
                            "googleusercontent.com" in photo_url):  
                            
                            # URL ini menghasilkan placeholder abu-abu
                            photo_url = f"https://placehold.co/600x337/E0E0E0/333333?text={urllib.parse.quote(str(item.get('name')))}&font=poppins"

                        st.image(photo_url) 
                        
                        st.markdown(f"""
                            <h3 style='height: 3.5em; margin: 0; color: var(--streamlit-theme-text-color); font-size: 1.25rem; font-weight: 600;'>
                                {item.get('name', 'Nama Tidak Tersedia')}
                            </h3>
                            """, unsafe_allow_html=True)
                        
                        st.caption(f"📍 {item.get('location', 'Lokasi Tidak Tersedia')}")
                        
                        col_meta1, col_meta2 = st.columns(2)
                        with col_meta1:
                            st.metric(label="Rating", value=f"⭐ {item['avg_rating']:.2f}")
                        with col_meta2:
                            st.metric(label="Relevansi", value=f"{item['top_vsm_score']:.3f}")
                        
                        st.write("")
                                                    
                        if st.button("Lihat Detail & Harga", key=f"btn_{index}", use_container_width=True):
                            st.session_state.selected_item = item # Simpan data item (dict)

        # --- 3. BLOK DIALOG (DITEMPATKAN SETELAH LOOP) ---
        # Ini akan berjalan jika 'selected_item' BUKAN None
        if st.session_state.selected_item:
            # Ambil item yang dipilih dari state
            item = st.session_state.selected_item
            
            # Tampilkan dialog dengan detail item
            @st.dialog(title=f"🏕️ {item.get('name', 'Detail')}")
            def tampilkan_detail_dialog():

                # Menampilkan Waktu Buka & Info Lokasi
                st.markdown(f"**📍 Lokasi:** {item.get('location', 'N/A')}")
                st.markdown(f"**🕒 Info Reservasi:** {item.get('waktu_buka', 'Info tidak tersedia')}")
                
                st.divider()

                st.markdown(f"**Estimasi Harga**")
                price_items_list = item.get('price_items', [])
                
                # Siapkan list untuk 4 kategori baru Anda
                item_wajib = []
                item_pokok = []
                item_mewah = []
                item_layanan = []

                if not price_items_list:
                    st.write("- Info harga tidak tersedia.")
                else:
                    # --- TAHAP 1: Kelompokkan Semua Item ---
                    for price_item in price_items_list:
                        try:
                            kategori = price_item.get('kategori', 'sewa mewah')
                            
                            # Tambahkan 'harga' sebagai int untuk menghindari error nanti
                            price_item['harga'] = int(price_item.get('harga', 0)) 
                            
                            if kategori == 'biaya wajib':
                                item_wajib.append(price_item)
                            elif kategori == 'sewa pokok':
                                item_pokok.append(price_item)
                            elif kategori == 'sewa mewah':
                                item_mewah.append(price_item)
                            elif kategori == 'layanan':
                                item_layanan.append(price_item)
                        except (ValueError, TypeError, AttributeError):
                            continue 

                    # --- TAHAP 2: Hitung Estimasi Dasar (Logika MIN + Pelacakan Nama) ---
                    total_estimasi_dasar = 0
                    # (BARU) List untuk menyimpan nama item yang dihitung
                    estimasi_items_names = []
                    
                    # 2a. Cari item TIKET termurah
                    item_tiket_list = [p for p in item_wajib if 'tiket' in p.get('item', '').lower()]
                    item_tiket_terbaik = min(item_tiket_list, key=lambda x: x['harga']) if item_tiket_list else None
                    
                    if item_tiket_terbaik:
                        total_estimasi_dasar += item_tiket_terbaik['harga']
                        estimasi_items_names.append(item_tiket_terbaik['item']) # Simpan nama

                    # 2b. Cari item PARKIR termurah
                    item_parkir_list = [p for p in item_wajib if 'parkir' in p.get('item', '').lower()]
                    item_parkir_terbaik = min(item_parkir_list, key=lambda x: x['harga']) if item_parkir_list else None

                    if item_parkir_terbaik:
                        total_estimasi_dasar += item_parkir_terbaik['harga']
                        estimasi_items_names.append(item_parkir_terbaik['item']) # Simpan nama

                    # 2c. Tambahkan biaya wajib LAINNYA (yang bukan tiket/parkir)
                    item_admin_lain = [p for p in item_wajib if 'tiket' not in p.get('item', '').lower() and 'parkir' not in p.get('item', '').lower()]
                    
                    for admin_item in item_admin_lain: 
                        total_estimasi_dasar += admin_item['harga']
                        estimasi_items_names.append(admin_item['item'])


                    # --- TAHAP 3: Tampilkan Semua Kategori ---
                    
                    if item_wajib:
                        st.markdown("**Biaya Wajib (Tiket, Parkir, dll)**")
                        for p in item_wajib: st.write(f"- {p.get('item')}: **Rp {p.get('harga', 0):,}**")

                    if item_pokok:
                        st.markdown("**Sewa Alat Pokok (Tenda, Matras, dll)**")
                        for p in item_pokok: st.write(f"- {p.get('item')}: **Rp {p.get('harga', 0):,}**")

                    if item_mewah:
                        st.markdown("**Sewa Alat Tambahan (Mewah)**")
                        for p in item_mewah: st.write(f"- {p.get('item')}: **Rp {p.get('harga', 0):,}**")
                    
                    if item_layanan:
                        st.markdown("**Layanan & Jasa (Katering, dll)**")
                        for p in item_layanan: st.write(f"- {p.get('item')}: **Rp {p.get('harga', 0):,}**")

                    # --- PERBAIKAN: Tampilkan Estimasi Dasar + Rinciannya ---
                    if total_estimasi_dasar > 0:
                        st.write("---")
                        st.markdown(f"**Estimasi Biaya Dasar (Wajib): Rp {total_estimasi_dasar:,}**")
                        
                        # Buat teks rincian
                        rincian_teks = " + ".join(estimasi_items_names)
                        st.caption(f"Estimasi dasar dihitung dari: {rincian_teks}")
                    
                st.write("") # Spasi
                
                st.markdown(f"**Fasilitas**")
                facilities_str = item.get('facilities', "") 
                
                if not facilities_str:
                    st.write("- Info fasilitas tidak tersedia.")
                else:
                    facilities_list = [f.strip() for f in re.split(r'[|,\n]', facilities_str) if f.strip()]
                    
                    if not facilities_list:
                        st.write("- Info fasilitas tidak tersedia.")
                    else:
                        for fac in facilities_list:
                            st.write(f"- {fac}")

                st.write("") # Spasi
                st.link_button("Buka di Google Maps ↗", item.get('gmaps_link', '#'), use_container_width=True)
                
                if st.button("Tutup", use_container_width=True, key="dialog_close"):
                    st.session_state.selected_item = None
                    st.rerun()

            tampilkan_detail_dialog()
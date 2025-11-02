import streamlit as st
import mesin_pencari
import pandas as pd
import urllib.parse 

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

# --- CSS KUSTOM ---
# (CSS Anda dari sebelumnya, tidak perlu diubah)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    
    html, body, [class*="st-"], [class*="css-"] {
        font-family: 'Poppins', sans-serif;
    }
    .main .block-container {
        padding-top: 10vh; 
        padding-bottom: 5rem;
    }
    [data-testid="stForm"] button[type="submit"] {
        display: none;
    }
    [data-testid="stAppViewContainer"] > section h1 {
        text-align: center;
        font-size: 3.5rem; 
        font-weight: 700;
    }
    [data-testid="stAppViewContainer"] > section [data-testid="stMarkdownContainer"]:nth-of-type(1) p {
        text-align: center;
        color: #FFFFFF; 
        font-weight: 300; 
        font-size: 1.1rem;
    }
    [data-testid="stTextInput"] > div > div {
        border: 1px solid #AAA; 
        border-radius: 50px; 
        background-color: #AAA; 
    }
    [data-testid="stTextInput"] input {
        color: #222; 
        padding-left: 20px; 
        font-weight: 400;
    }
    [data-testid="stTextInput"] > div > div:has(input:focus) {
        border-color: #4285F4; 
        box-shadow: 0 0 5px rgba(66, 133, 244, 0.5);
    }
    div[data-testid="stVerticalBlock"] > [data-testid="stContainer"] > [data-testid="stVerticalBlock"] {
        border-radius: 1rem; 
        border: 1px solid #eee; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); 
        transition: transform 0.2s ease; 
        background-color: #FFFFFF; 
    }
    div[data-testid="stVerticalBlock"] > [data-testid="stContainer"]:hover > [data-testid="stVerticalBlock"] {
        transform: translateY(-5px); 
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
    }
    div[data-testid="stImage"] > img {
        border-radius: 1rem 1rem 0 0; 
        object-fit: cover;
        height: 180px; 
        width: 100%;
    }
    [data-testid="stVerticalBlock"] > [data-testid="stContainer"] [data-testid="stBlock"] {
        padding: 1rem; 
    }
    div[data-testid="stLinkButton"] a {
        width: 100%;
        text-align: center;
        border-radius: 50px;
    }
    div[data-testid="stButton"] button {
        width: 100%;
        border-radius: 50px;
        background-color: #f0f2f6; 
        color: #333; 
        border: 1px solid #ddd;
    }
    div[data-testid="stButton"] button:hover {
        background-color: #e9ecef;
        border: 1px solid #ccc;
    }
    div[data-testid="stModal"] .st-emotion-cache-1fsvtu1 {
        background-color: #eee;
        color: #333;
        border: none;
        border-radius: 16px;
        padding: 5px 12px;
        font-size: 0.9rem;
        margin-right: 5px;
        margin-bottom: 5px;
        display: inline-block;
    }
    </style>
    """, unsafe_allow_html=True)

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

#st.sidebar.title("Panel Admin")
#admin_password = st.sidebar.text_input("Masukkan Password Admin", type="password")

#if admin_password == st.secrets.get("ADMIN_PASSWORD", ""):
#    st.sidebar.success("Mode Admin Aktif  unlocked")
#    st.sidebar.subheader("📊 Riwayat Pencarian (50 Terbaru)")
#    
#    try:
#        # Panggil fungsi GSheets untuk MEMBACA (load)
#        df_log = load_logs_gsheets()
#        st.sidebar.dataframe(df_log)
#        
#    except Exception as e:
#        st.sidebar.error(f"Gagal mengambil data log: {e}")
#elif admin_password:
#    st.sidebar.error("Password admin salah.")

# ======================================================================
# TAMPILAN UTAMA
# ======================================================================

# Gunakan session state untuk menyimpan kueri
if 'query' not in st.session_state:
    st.session_state.query = ""
if 'search_performed' not in st.session_state:
    st.session_state.search_performed = False

# --- Judul Utama ---
# Buat layout kolom agar search bar bisa di tengah
col_logo1, col_logo2, col_logo3 = st.columns([2, 3, 2])
with col_logo2:
    st.title("🏕️ Cari Kemah")
    st.subheader("Mesin Pencari VSM untuk Tempat Kemah")
    st.write("") # Spasi

col1, col_main, col3 = st.columns([1, 2, 1]) 
with col_main:
    with st.form(key="search_form"):
        query_input = st.text_input(
            "Cari tempat kemah...", 
            placeholder="Ketik lalu tekan 'Enter'...",
            label_visibility="collapsed"
        )
        tombol_cari = st.form_submit_button(label="Cari")

# ======================================================================
# 5. LOGIKA & TAMPILAN HASIL (PERBAIKAN STATE MANAGEMENT)
# ======================================================================

# --- Inisialisasi state jika belum ada ---
if 'search_performed' not in st.session_state:
    st.session_state.search_performed = False
if 'results_df' not in st.session_state:
    st.session_state.results_df = pd.DataFrame()
if 'modal_data' not in st.session_state:
    st.session_state.modal_data = None
if 'query_info' not in st.session_state:
    st.session_state.query_info = {}

# --- 1. LOGIKA SAAT PENCARIAN BARU DILAKUKAN ---
if tombol_cari and query_input:
    st.session_state.search_performed = True
    st.session_state.modal_data = None # Tutup modal lama jika ada
    
    with st.spinner("⏳ Menganalisis ulasan dan mencari rekomendasi..."):
        vsm_tokens, intent, region = mesin_pencari.analyze_full_query(query_input)
        results = mesin_pencari.search_by_keyword(vsm_tokens, intent, region)
        
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
            
            for index, item in df_results.iterrows():
                col = grid_cols[index % 3]
                
                with col:
                    with st.container(border=True):
                        # Tambahkan fallback untuk foto 'nan'
                        photo_url = item['photo_url']
                        if not isinstance(photo_url, str) or pd.isna(photo_url):
                            photo_url = f"https://placehold.co/400x200/556B2F/FFFFFF?text={urllib.parse.quote(item['name'])}&font=poppins"
                        st.image(photo_url)
                        
                        st.markdown(f"""
                            <h3 style='height: 3.5em; margin: 0; color: black; font-size: 1.25rem; font-weight: 600;'>
                                {item['name']}
                            </h3>
                            """, unsafe_allow_html=True)
                        st.caption(f"📍 {item['location']}")
                        
                        col_meta1, col_meta2 = st.columns(2)
                        with col_meta1:
                            st.metric(label="Rating", value=f"⭐ {item['avg_rating']:.2f}")
                        with col_meta2:
                            st.metric(label="Relevansi", value=f"{item['top_vsm_score']:.3f}")
                        
                        st.write("")
                        
                        # Tombol ini sekarang hanya mengatur state
                        if st.button("Lihat Detail", key=f"detail_{index}", use_container_width=True):
                            st.session_state.modal_data = item.to_dict()
                            st.rerun() # Paksa rerun untuk membuka modal
                
                if (index + 1) % 3 == 0:
                    st.write("") 

# --- 3. LOGIKA UNTUK MENAMPILKAN MODAL (DI LUAR LOOP) ---
# (Ini akan berjalan di *setiap* rerun)
if st.session_state.modal_data:
    item = st.session_state.modal_data # Ambil data yang disimpan
    
    # Buat modal
    modal = st.modal(f"Detail untuk {item['name']}")
    with modal:

        photo_url = item['photo_url']
        if not isinstance(photo_url, str) or pd.isna(photo_url):
            photo_url = f"https://placehold.co/400x200/556B2F/FFFFFF?text={urllib.parse.quote(item['name'])}&font=poppins"
        st.image(photo_url) 
        
        st.subheader("Estimasi Harga")
        st.info(f"**{item['price']}**")

        st.subheader("Fasilitas")
        facilities_list = [f.strip() for f in str(item['facilities']).split(',')]
        st.write(" ".join(f"`{fac}`" for fac in facilities_list))

        st.write("")
        st.link_button("Buka di Google Maps ↗", item['gmaps_link'], use_container_width=True)
        
        # Tombol tutup di dalam modal
        if st.button("Tutup"):
            st.session_state.modal_data = None
            st.rerun() # Paksa rerun untuk menutup modal
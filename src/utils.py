import pandas as pd
import os
import joblib
import streamlit as st
from .vsm_structures import Node, SlinkedList
from datetime import datetime

# Dapatkan path ke folder 'src' saat ini
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
# Dapatkan path ke folder ROOT (satu level di atas 'src')
BASE_DIR = os.path.dirname(SRC_DIR)

def load_map_from_csv(filename):
    """
    Memuat file CSV (kolom A: key, kolom B: value) ke dalam dictionary.
    Fungsi ini mengabaikan baris yang diawali '#' (untuk komentar)
    dan mengabaikan kolom ekstra (seperti kolom 'kategori').
    """

    # Tentukan path file absolut
    filepath = os.path.join(BASE_DIR, 'Kamus', filename)

    try:
        # Cek apakah file ada
        if not os.path.exists(filepath):
             print(f"!!! GAGAL: File Kamus tidak ditemukan di: {filepath}")
             return {}

        # 'comment=#' memberi tahu pandas untuk mengabaikan baris yang diawali #
        df = pd.read_csv(filepath, comment='#', dtype=str).fillna('')
        
        # Ambil nama kolom pertama (A) dan kedua (B)
        key_col = df.columns[0]
        value_col = df.columns[1]
        
        # Hapus baris yang mungkin kosong di kolom A atau B
        df = df.dropna(subset=[key_col, value_col])
        
        # Buat dictionary: Kolom A jadi key, Kolom B jadi value
        mapper_dict = pd.Series(df[value_col].values, index=df[key_col]).to_dict()
        
        print(f"Berhasil memuat {len(mapper_dict)} aturan dari {filepath}")
        return mapper_dict
        
    except FileNotFoundError:
        print(f"!!! PERINGATAN: File konfigurasi {filepath} tidak ditemukan. Menggunakan dictionary kosong.")
        return {}
    except Exception as e:
        print(f"!!! ERROR saat memuat {filepath}: {e}")
        return {}
    
def load_assets():
    """Memuat aset VSM dari folder assets/ menggunakan path absolut."""
    assets_dir = os.path.join(BASE_DIR, 'Assets')
    
    try:
        # Memuat tiga aset utama
        IDF_SCORES = joblib.load(os.path.join(assets_dir, 'idf_scores.pkl'))
        VSM_INDEX_TF = joblib.load(os.path.join(assets_dir, 'vsm_index_tf.pkl'))
        DF_METADATA = joblib.load(os.path.join(assets_dir, 'df_metadata.pkl'))
        
        print("✅ Aset VSM berhasil dimuat.")
        return IDF_SCORES, VSM_INDEX_TF, DF_METADATA
    
    except FileNotFoundError:
        print(f"❌ ERROR: File aset .pkl tidak ditemukan di '{assets_dir}'.")
        print("   Pastikan Anda sudah menjalankan skrip indexing dan menyimpan file .pkl di folder 'assets'.")
        return None, None, None
    except Exception as e:
        print(f"❌ ERROR saat memuat aset VSM: {e}")
        return None, None, None
    
def log_pencarian_gsheets(query, tokens, intent, region):
    """Mencatat detail pencarian ke Google Sheets."""
    try:
        conn = st.connection("gsheets", type="gsheets")

        # Buat data baru dalam satu baris (DataFrame)
        data_baru = pd.DataFrame({
            "timestamp": [datetime.now()],
            "queri_mentah": [query],
            "vsm_tokens_final": [' '.join(tokens)],
            "intent_terdeteksi": [str(intent)],
            "region_terdeteksi": [str(region)]
        })

        # Tambahkan baris baru ke sheet
        # 'worksheet="Sheet1"' -> Sesuaikan dengan nama sheet Anda
        conn.append_rows(worksheet="LogData", data=data_baru)

    except Exception as e:
        st.warning(f"Gagal mencatat riwayat GSheets: {e}")

def load_logs_gsheets():
    """
    Mengambil data log dari Google Sheets untuk dashboard admin.
    """
    try:
        conn = st.connection("gsheets", type="gsheets")
        # PASTIKAN NAMA "LogData" SAMA DENGAN NAMA TAB DI GOOGLE SHEET ANDA
        # ttl=300 -> Cache data selama 5 menit
        df = conn.read(worksheet="LogData", ttl=300)
        
        # Hapus baris kosong jika ada
        df = df.dropna(how="all")
        
        # Urutkan dari yang terbaru (asumsi data baru ditambah di akhir)
        df = df.sort_index(ascending=False)
        
        return df.head(50) # Ambil 50 terbaru
    except Exception as e:
        st.sidebar.error(f"Gagal memuat log GSheets: {e}")
        return pd.DataFrame() # Kembalikan DataFrame kosong

LOG_FILE_PATH = os.path.join(BASE_DIR, 'Riwayat', 'riwayat_pencarian.csv')
LOG_COLS = ['timestamp', 'query_mentah', 'vsm_tokens', 'intent', 'region']

def log_pencarian_csv(query, tokens, intent, region):
    """
    Mencatat kueri pencarian ke file CSV lokal di folder /Riwayat.
    Dibuat agar anti-gagal (tidak akan meng-crash aplikasi utama).
    """
    try:
        # 1. Pastikan folder 'Riwayat' ada
        os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
        
        # 2. Siapkan data baru
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        tokens_str = ' '.join(tokens)
        data_baru = pd.DataFrame(
            [[timestamp, query, tokens_str, str(intent), str(region)]], 
            columns=LOG_COLS
        )
        
        # 3. Cek apakah file ada (untuk menentukan perlu header atau tidak)
        file_exists = os.path.exists(LOG_FILE_PATH)
        
        # 4. Tulis/Append ke CSV
        data_baru.to_csv(
            LOG_FILE_PATH, 
            mode='a', # 'a' = append (menambahkan)
            header=not file_exists, # Hanya tulis header jika file baru
            index=False
        )
    except Exception as e:
        # PENTING: Jangan crash aplikasi utama jika logging gagal
        print(f"⚠️ GAGAL mencatat riwayat ke CSV: {e}")
        # Di Streamlit Cloud, ini hanya akan muncul di log, tidak di UI
        st.toast(f"Gagal mencatat riwayat: {e}", icon="⚠️")

def baca_riwayat_csv(limit=50):
    """
    Membaca file log CSV untuk ditampilkan di dashboard admin.
    """
    try:
        df = pd.read_csv(LOG_FILE_PATH)
        # Urutkan dari terbaru ke terlama dan ambil limit
        return df.iloc[::-1].head(limit)
    except FileNotFoundError:
        # Jika file belum ada, kembalikan DataFrame kosong
        return pd.DataFrame(columns=LOG_COLS)
    except Exception as e:
        print(f"⚠️ GAGAL membaca riwayat CSV: {e}")
        return pd.DataFrame(columns=LOG_COLS)

#def log_pencarian_sql(query, tokens, intent, region):
    """
    Mencatat detail pencarian ke database SQL (Supabase).
    ... (fungsi ini tidak berubah) ...
    """
    try:
        # 1. Ubah list token menjadi satu string agar bisa disimpan
        tokens_str = ' '.join(tokens)
        
        # 2. Inisialisasi koneksi (nama "supabase_db" dari secrets.toml)
        conn = st.connection("supabase_db", type="sql")

        # 3. Gunakan .session untuk eksekusi perintah INSERT
        with conn.session as s:
            
            # 4. Siapkan perintah SQL (sesuai tabel BARU yang kita buat)
            # Menggunakan :nama_variabel untuk keamanan (SQL Injection)
            sql = text("""
                INSERT INTO riwayat_pencarian 
                    (kueri_mentah, vsm_tokens, intent_terdeteksi, region_terdeteksi)
                VALUES 
                    (:kueri, :tokens, :intent, :region)
            """)
            
            # 5. Eksekusi perintah dengan data yang sebenarnya
            s.execute(sql, {
                "kueri": query,
                "tokens": tokens_str,
                "intent": str(intent),
                "region": str(region)
            })
            
            # 6. Commit (simpan) perubahan ke database
            s.commit()
            
    except Exception as e:
        # Jika gagal, jangan buat aplikasi crash.
        # Cukup tampilkan peringatan di log terminal/Streamlit.
        st.warning(f"Gagal mencatat riwayat pencarian SQL: {e}")
# --- app.py ---

from flask import Flask, request, jsonify, render_template
import mesin_pencari # Import modul mesin pencari Anda
import nltk

# --- PANGGIL INISIALISASI SEKALI SAAT SERVER MULAI ---
mesin_pencari.initialize_mesin() 

app = Flask(__name__,
            template_folder='Templates',
            static_folder='Static')

# --- ENDPOINT HALAMAN UTAMA ---
@app.route('/', methods=['GET'])
def index():
    # Memberitahu Flask untuk mencari dan mengirimkan 'index.html' dari folder 'templates'
    return render_template('index.html')

# --- ENDPOINT API PENCARIAN ---
@app.route('/search', methods=['GET'])
def handle_search():
    # 1. Ambil query dari parameter URL (?q=...)
    query = request.args.get('q') 
    if not query:
        return jsonify({"error": "Parameter 'q' (query) tidak ditemukan"}), 400 # HTTP 400 Bad Request
        
    try:
        # 2. Analisis query (memanggil fungsi dari mesin_pencari.py)
        vsm_tokens, intent, region = mesin_pencari.analyze_full_query(query)
        
        # 3. Catat pencarian ini ke riwayat (memanggil fungsi dari mesin_pencari.py)
        mesin_pencari.log_pencarian(query, vsm_tokens, intent, region)
        
        # 4. Lakukan pencarian VSM (memanggil fungsi dari mesin_pencari.py)
        results = mesin_pencari.search_by_keyword(vsm_tokens, intent, region)
        
        # 5. Kembalikan hasil sebagai JSON
        return jsonify(results)

    except Exception as e:
        # Menangani error tak terduga selama proses pencarian
        print(f"!!! ERROR saat memproses query '{query}': {e}")
        # Mengembalikan pesan error umum ke pengguna
        return jsonify({"error": "Terjadi kesalahan internal saat memproses pencarian."}), 500 # HTTP 500 Internal Server Error

# --- BLOK UNTUK MENJALANKAN SERVER (Untuk Tes Lokal) ---
if __name__ == '__main__':
    # 'debug=True' akan otomatis me-restart server jika Anda mengubah kode.
    # Jangan gunakan 'debug=True' saat deployment production.
    #app.run(debug=True, port=5000) # Server akan berjalan di http://127.0.0.1:5000/
    pass
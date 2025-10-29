def analyze_full_query(query_text):
    """
    Menganalisis query untuk intent, region, dan teks VSM terakhir.
    """
    
    # 1. Deteksi Intent
    # Ini membersihkan query dari frasa intent, misal "tempat kemah terbaik"
    query_after_intent, special_intent = detect_intent(query_text)
    
    # 2. Deteksi Region
    # Ini membersihkan query dari frasa region, misal "jawa tengah"
    final_vsm_text, region_filter = detect_region_and_filter_query(query_after_intent)
    
    # 3. Preprocessing Teks VSM
    vsm_tokens = full_preprocessing(final_vsm_text)

    # Tambahan pengecekan khusus jika ada filter region
    if region_filter:
        # Gunakan kata yang sudah di-stem
        generic_fluff_words = {'cari', 'tampil', 'lihat', 'berikan', 'saran', 'rekomendasikan'} 
        
        # Cek apakah vsm_tokens HANYA berisi kata-kata fluff
        if vsm_tokens and all(token in generic_fluff_words for token in vsm_tokens):
            vsm_tokens = [] # Kosongkan token, jangan cari VSM
    
    # Jika token kosong setelah semua filter (misal query-nya hanya "terbaik di jogja")
    if not vsm_tokens and (special_intent or region_filter):
         # Beri kata kunci default agar VSM tidak error
        vsm_tokens = ['kemah'] 

        # Jika intent awalnya kosong TAPI region ada,
        # berarti pengguna HANYA ingin filter region. Ubah intent ke 'ALL'.
        if not special_intent and region_filter:
            special_intent = 'ALL'
        
    return vsm_tokens, special_intent, region_filter

# --- 5. FUNGSI VSM RANKING MURNI ---
def search_by_keyword(query_tokens, special_intent, region_filter):
    """
    Melakukan pencarian berdasarkan token VSM, intent, dan filter region.
    """
    # Tangani kasus special_intent 'ALL'
    if special_intent == 'ALL':
        
        # 1. Ambil semua tempat unik langsung dari metadata
        df_unique_places = df_metadata[['Nama_Tempat', 'Lokasi', 'Avg_Rating']].drop_duplicates(subset='Nama_Tempat').copy()
        
        # 2. Terapkan filter regional jika ada
        if region_filter:
            # Menggunakan .str.contains() untuk mencocokkan substring (misal: 'diy' atau 'semarang')
            df_unique_places = df_unique_places[df_unique_places['Lokasi'].str.lower().str.contains(region_filter, na=False)]

        # 3. Urutkan berdasarkan Rating Tertinggi (sebagai default untuk 'ALL')
        df_unique_places = df_unique_places.sort_values(by='Avg_Rating', ascending=False)
        
        # 4. Ubah format ke dictionary standar
        final_recommendations = []
        for _, row in df_unique_places.iterrows():
            final_recommendations.append({
                'name': row['Nama_Tempat'],
                'location': row['Lokasi'],
                'avg_rating': row['Avg_Rating'],
                'top_vsm_score': 0.0  # Skor VSM 0.0 karena VSM tidak digunakan
            })
        
        # Langsung kembalikan hasilnya
        return final_recommendations

    # 1. Preprocessing Query
    if not query_tokens:
        return []
    
    # 2. Query Vectorization (TF-IDF)
    query_tf = {}
    for word in query_tokens:
        query_tf[word] = query_tf.get(word, 0) + 1
        
    query_weights = {}
    involved_docs = set()
    
    for term, tf in query_tf.items():
        if term in idf_scores:
            query_weights[term] = tf * idf_scores[term]
            
            # Collect all documents involved from the Index
            current_node = linked_list_data[term].head.nextval
            while current_node is not None:
                involved_docs.add(current_node.doc)
                current_node = current_node.nextval
        else:
            continue

    if not involved_docs:
        return []

    # 3. Cosine Similarity (Dot Product Only)
    doc_scores = {doc_id: 0 for doc_id in involved_docs}
    
    # Calculate DOT PRODUCT: Sum(W(t,d) * W(t,q))
    for term, W_q in query_weights.items():
        current_node = linked_list_data[term].head.nextval
        while current_node is not None:
            doc_id = current_node.doc
            W_d = current_node.freq # TF-IDF weight W(t,d)
            doc_scores[doc_id] += W_d * W_q
            current_node = current_node.nextval
            
    # 4. Ranking Ulasan (Doc ID)
    ranked_results_by_doc = sorted(doc_scores.items(), key=lambda item: item[1], reverse=True)
    
    # 5. Agregasi ke Nama Tempat (Mengambil ulasan paling relevan per tempat)
    final_recommendations = []
    unique_names = set()
    
    for doc_id, vsm_score in ranked_results_by_doc:
        try:
            meta = df_metadata.loc[doc_id]
        except KeyError:
            continue
        
        # Filter berdasarkan region jika diminta (opsional)
        if region_filter:
            if region_filter not in meta['Lokasi'].lower():
                continue # Skip dokumen yang tidak sesuai region
            
        name = meta['Nama_Tempat']
        
        if name not in unique_names:
            unique_names.add(name)
            final_recommendations.append({
                'name': name,
                'location': meta['Lokasi'],
                'avg_rating': meta['Avg_Rating'],
                'top_vsm_score': vsm_score
            })

    # 6. Logika Intent
    # Terapkan sorting berdasarkan intent setelah VSM selesai
    if special_intent == 'RATING_TOP':
        # Urutkan berdasarkan Avg_Rating (Tertinggi ke Terendah)
        final_recommendations.sort(key=lambda x: x['avg_rating'], reverse=True)
    
    elif special_intent == 'RATING_BOTTOM':
        # Urutkan berdasarkan Avg_Rating (Terendah ke Tertinggi)
        final_recommendations.sort(key=lambda x: x['avg_rating'], reverse=False)
            
    return final_recommendations

# --- 6. FUNGSI UNTUK RIWAYAT PENCARIAN ---

NAMA_FOLDER_RIWAYAT = 'Riwayat'
NAMA_FILE_RIWAYAT = os.path.join(NAMA_FOLDER_RIWAYAT, 'riwayat_pencarian.csv')

# Definisikan header untuk file CSV
HEADER_RIWAYAT = ['timestamp', 'query_mentah', 'vsm_tokens_final', 'intent_terdeteksi', 'region_terdeteksi']

def log_pencarian(query, tokens, intent, region):
    """Menyimpan detail pencarian ke file CSV."""
    
    try:
        # 1. Dapatkan waktu saat ini
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 2. Ubah daftar token menjadi string agar mudah dibaca
        # misal: ['kamar', 'mandi'] -> "kamar mandi"
        tokens_str = ' '.join(tokens)
        
        # 3. Siapkan baris data yang akan ditulis
        data_row = [timestamp, query, tokens_str, str(intent), str(region)]
        
        # 4. Cek apakah file sudah ada (untuk menentukan perlu header atau tidak)
        file_exists = os.path.isfile(NAMA_FILE_RIWAYAT)
        
        # 5. Buka file dalam mode 'append' (a)
        with open(NAMA_FILE_RIWAYAT, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Jika file baru dibuat, tulis headernya dulu
            if not file_exists:
                writer.writerow(HEADER_RIWAYAT)
                
            # Tulis baris data pencarian
            writer.writerow(data_row)
            
    except Exception as e:
        # Cetak peringatan jika gagal, tapi jangan hentikan program
        print(f"\n!!! PERINGATAN: Gagal menyimpan riwayat pencarian: {e}")
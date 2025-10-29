def load_map_from_csv(filepath):
    """
    Memuat file CSV (kolom A: key, kolom B: value) ke dalam dictionary.
    Fungsi ini mengabaikan baris yang diawali '#' (untuk komentar)
    dan mengabaikan kolom ekstra (seperti kolom 'kategori').
    """
    try:
        # 'comment=#' memberi tahu pandas untuk mengabaikan baris yang diawali #
        df = pd.read_csv(filepath, comment='#')
        
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
    
    # --- 3. APLIKASI PREPROCESSING & HITUNG DF & IDF (INDEXING PHASE 1) ---
# Pastikan dataset sudah dimuat di df_corpus
df_corpus['Teks_Mentah'] = df_corpus['Teks_Mentah'].fillna('')
df_corpus['Clean_Tokens'] = df_corpus['Teks_Mentah'].apply(full_preprocessing)

N = len(df_corpus)
df_counts = {} # Document Frequency

for tokens in df_corpus['Clean_Tokens']:
    for word in set(tokens): 
        df_counts[word] = df_counts.get(word, 0) + 1

idf_scores = {}
for term, count in df_counts.items():
    idf_scores[term] = math.log10(N / count)

# --- 4. BUILDING THE INVERTED INDEX WITH TF-IDF (INDEXING PHASE 2) ---
linked_list_data = {}
unique_words_all = set(df_counts.keys())

for word in unique_words_all:
    linked_list_data[word] = SlinkedList()
    linked_list_data[word].head = Node(docId=0, freq=None) 

for index, row in df_corpus.iterrows():
    doc_id = row['Doc_ID']
    tokens = row['Clean_Tokens']
    
    tf_in_doc = {}
    for word in tokens:
        tf_in_doc[word] = tf_in_doc.get(word, 0) + 1

    for term, tf in tf_in_doc.items():
        tfidf = tf * idf_scores[term]
        
        linked_list = linked_list_data[term].head
        while linked_list.nextval is not None:
            linked_list = linked_list.nextval
        
        linked_list.nextval = Node(docId=doc_id, freq=tfidf)

# Mapping Doc ID to Name and Rating for final result
df_metadata = df_corpus[['Doc_ID', 'Nama_Tempat', 'Lokasi', 'Rating']].copy()
avg_rating_per_place = df_metadata.groupby('Nama_Tempat')['Rating'].mean().reset_index()
avg_rating_per_place.rename(columns={'Rating': 'Avg_Rating'}, inplace=True)
df_metadata = df_metadata.merge(avg_rating_per_place, on='Nama_Tempat', how='left')
df_metadata.set_index('Doc_ID', inplace=True)
# Definisi Pemegangan Frasa Kompleks
def substitute_complex_phrases(text, phrase_map):
    """Mengganti frasa kompleks dengan single token sebelum tokenisasi."""
    # Pastikan substitusi dilakukan pada teks lowercase
    text_lower = text.lower()

    sorted_phrases = sorted(phrase_map.items(), key=lambda item: len(item[0]), reverse=True)
    
    for phrase, token in sorted_phrases:
        try:
            # re.escape() mengamankan frasa jika mengandung karakter regex
            regex_phrase = r'\b' + re.escape(str(phrase)) + r'\b'
            
            # Ganti hanya frasa yang ditemukan sebagai "kata utuh"
            text_lower = re.sub(regex_phrase, str(token), text_lower)
            
        except re.error:
            # Fallback ke replace() biasa jika ada error regex
            text_lower = text_lower.replace(str(phrase), str(token))
        
    return text_lower

# Muat PHRASE_MAP dari file eksternal
PHRASE_MAP = load_map_from_csv('Kamus\config_phrase_map.csv')

# Muat REGION_MAP dari file eksternal
REGION_MAP = load_map_from_csv('Kamus\config_region_map.csv')

def detect_region_and_filter_query(query_text):
    """
    Menganalisis query untuk menentukan apakah mengandung niat regional.
    Mengembalikan query yang sudah difilter (tanpa kata regional) dan kode region.
    """
    
    query_text_lower = query_text.lower()
    detected_region = None
    
    # Deteksi Region
    for term, region in REGION_MAP.items():
        if term in query_text_lower:
            detected_region = region
            query_text_lower = query_text_lower.replace(term, '') # Hapus kata regional
            # Break setelah region pertama terdeteksi (asumsi hanya 1 region per query)
            break 
            
    # Rebuild Query tanpa kata regional (untuk VSM)
    # Hapus spasi berlebihan dan filter token kosong
    filtered_query_text = " ".join([word for word in query_text_lower.split() if word])
    
    return filtered_query_text, detected_region

# Muat SPECIAL_INTENT_MAP dari file eksternal
SPECIAL_INTENT_MAP = load_map_from_csv('Kamus\config_special_intent.csv')

def detect_intent(query_text):
    """
    Menganalisis query untuk menentukan niat khusus (ALL/RATING).
    Mengembalikan query VSM yang sudah bersih, dan special_intent.
    """
    query_text_lower = query_text.lower()
    special_intent = None
    
    # 1. Deteksi Niat Khusus (ALL/RATING)
    for term, intent in SPECIAL_INTENT_MAP.items():
        if term in query_text_lower:
            special_intent = intent
            query_text_lower = query_text_lower.replace(term, '')
            break
            
    # 3. Rebuild Query VSM
    filtered_query_text = " ".join([word for word in query_text_lower.split() if word])
    
    return filtered_query_text, special_intent

# --- 2. DEFENISI FUNGSI HELPER & VSM CLASSES ---
# Fungsi Pembersihan Karakter Spesial
def remove_special_characters(text):
    if not isinstance(text, str):
        return "" 
    regex = re.compile(r'[^a-zA-Z0-9\s]')
    return re.sub(regex, '', text)

# Fungsi Proses Penuh (Preprocessing)
def full_preprocessing(text):
    if not isinstance(text, str):
        return []
        
    cleaned_text = remove_special_characters(text)
    cleaned_text = re.sub(r'\d', '', cleaned_text)

    text_with_phrases = substitute_complex_phrases(cleaned_text, PHRASE_MAP)
    
    # Simple Tokenization (split by whitespace) & Lowercasing
    words = text_with_phrases.lower().split()
    
    words = [w for w in words if w not in stopwords_id]
    
    # Stemming
    stemmed_words = [stemmer.stem(w) for w in words]
    
    final_words = [w for w in stemmed_words if len(w) > 1]
    return final_words

# Inverted Index Classes
class Node:
    def __init__(self, docId, freq=None):
        self.freq = freq # TF-IDF weight
        self.doc = docId
        self.nextval = None

class SlinkedList:
    def __init__(self, head=None):
        self.head = head
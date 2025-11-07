# 🏕️ Proyek UTS STKI: CampGround Search (Boolean & VSM)

Proyek ini mengimplementasikan dan mengevaluasi sistem temu kembali informasi (STKI) klasik, termasuk model **Boolean** dan **Vector Space Model (VSM)**. Sistem ini dibangun di atas korpus ulasan tempat *camping* di Jawa Tengah & DIY.

Proyek ini memiliki dua fungsi:
1.  **Memenuhi Persyaratan UTS STKI (A11.4703):** Dengan mengimplementasikan `search.py` (CLI), `eval.py` (Evaluasi Metrik), dan perbandingan skema bobot.
2.  **Sebagai Portofolio (RAG):** Logika inti VSM dari proyek ini juga digunakan sebagai *retriever* untuk aplikasi web RAG (Retrieval-Augmented Generation) berbasis Streamlit.

**URL Deployment (Aplikasi Web RAG):**
[https://candrawij-tempat-kemah-web-v2-streamlit-app-dbcga0.streamlit.app/](https://candrawij-tempat-kemah-web-v2-streamlit-app-dbcga0.streamlit.app/)

---

## 1. Arsitektur & Desain Sistem (Soal 01)

Sistem ini dirancang dengan logika inti yang terpisah di dalam folder `src/`, yang memungkinkan penggunaan kembali oleh berbagai "titik masuk" (entry points):

* **`src/` (Logika Inti):** Berisi semua modul logika murni untuk preprocessing (`preprocessing.py`), VSM (`mesin_pencari.py`), Boolean (`boolean_ir.py`), dan utilitas (`utils.py`).
* **`build_index.py` (Indexing):** Skrip *offline* yang membaca `Documents/` dan membuat indeks di `Assets/`.
* **`eval.py` (Evaluasi UTS):** Skrip yang mengimpor logika `src/` untuk menjalankan evaluasi metrik formal terhadap `gold_set.json`.
* **`search.py` (CLI UTS):** *Orchestrator* CLI (Soal 05) yang mengimpor `src/` untuk menjalankan pencarian VSM atau Boolean.
* **`streamlit_app.py` (Web App):** Aplikasi web RAG yang mengimpor `src/mesin_pencari.py` untuk mengambil konteks (dokumen) sebelum diserahkan ke LLM.

## 2. Struktur File

Struktur repositori ini dirancang untuk memisahkan data, aset, logika inti, dan skrip yang dapat dieksekusi.

CampGround Search/
├── Assets/                 # Output indeks .pkl (Hasil build_index.py)
│   ├── boolean_index.pkl
│   ├── df_metadata.pkl
│   ├── idf_scores.pkl
│   └── vsm_index_tf.pkl
├── Documents/              # Data mentah (korpus)
│   ├── corpus_master.csv
│   └── info_tempat.csv
├── Kamus/                  # Kamus untuk preprocessing
│   └── ...
├── src/                    # Modul Logika Inti
│   ├── __init__.py         # (Penting agar 'src' dikenali sebagai paket)
│   ├── boolean_ir.py       # (Logika Model Boolean)
│   ├── mesin_pencari.py    # (Logika Model VSM & Augmentasi RAG
│   ├── preprocessing.py    # (Logika preprocessing teks)
│   ├── utils.py            # (Fungsi helper, pemuat aset)
│   └── vsm_structures.py   # (Class Node & SlinkedList)
│
├── .gitignore              # (Mengabaikan .venv, pycache, dll.)
├── build_index.py          # [BISA DIJALANKAN] Skrip untuk build indeks
├── eval.py                 # [BISA DIJALANKAN] Skrip evaluasi
├── gold_set.json           # (Kunci jawaban manual untuk eval.py)
├── README.md               
├── requirements.txt        # (Dependensi Python)
├── search.py               # [BISA DIJALANKAN] CLI Orchestrator
├── streamlit_app.py        # [BISA DIJALANKAN] Aplikasi Web (Portofolio)
└── style.css               # (CSS untuk Streamlit)

## 3. Metode & Implementasi

### 3.1. Document Preprocessing (Soal 02)
Semua dokumen dan kueri melewati pipeline preprocessing yang ada di `src/preprocessing.py`. Tahapannya meliputi:
1.  **Case Folding:** Mengubah semua teks menjadi huruf kecil.
2.  **Normalization:** Menggunakan kamus dari `Kamus/` untuk mengganti slang, frasa, dan typo (misal: "kmr mandi" -> "kamarmandi").
3.  **Tokenization:** Memecah teks menjadi token (kata).
4.  **Stopword Removal:** Menghapus *stopwords* bahasa Indonesia menggunakan `nltk`, dengan modifikasi untuk **mempertahankan kata negasi** (seperti 'tidak', 'kurang', 'jangan') agar makna tetap terjaga.
5.  **Stemming:** Mengubah kata ke bentuk dasarnya menggunakan `Sastrawi`.

### 3.2. Boolean Retrieval Model (Soal 03)
* **Implementasi:** `src/boolean_ir.py`
* **Indeks:** Selama indexing, `boolean_index.pkl` dibuat sebagai *dictionary* Python, memetakan `term` ke `set()` dari `Doc_ID` yang mengandung *term* tersebut.
* **Logika:** Pencarian dilakukan dengan *parser* sederhana yang menerapkan operasi `set` Python: `intersection` (AND), `union` (OR), dan `difference` (NOT).

### 3.3. Vector Space Model (Soal 04 & 05)
* **Implementasi:** `src/mesin_pencari.py`
* **Indeks:** VSM menggunakan dua file aset:
    1.  `idf_scores.pkl`: Menyimpan skor IDF ( $idf_t$ ) untuk setiap *term*.
    2.  `vsm_index_tf.pkl`: *Inverted index* (diimplementasikan sebagai *Linked List* dari `vsm_structures.py`) yang memetakan `term` ke *postings list* berisi `(Doc_ID, raw_tf)`.
* **Pembobotan:** Bobot dokumen ( $W_{d,t}$ ) dihitung secara **dinamis/on-the-fly** saat pencarian. Ini memungkinkan perbandingan skema bobot (Soal 05) menggunakan indeks yang sama.
* **Formula yang Digunakan:**
    * **Skema 1 (TF-IDF Standar):**
        $$
        W_{t,d} = tf_{t,d} \times idf_t = tf_{t,d} \times \log_{10}(\frac{N}{df_t})
        $$
    * **Skema 2 (Sublinear TF-IDF):**
        $$
        W_{t,d} = (1 + \log_{10}(tf_{t,d})) \times \log_{10}(\frac{N}{df_t})
        $$
* **Ranking:** Peringkat dihitung menggunakan *dot product* antara vektor kueri ( $W_{t,q}$ ) dan vektor dokumen ( $W_{t,d}$ ), yang ekuivalen dengan Cosine Similarity (tanpa normalisasi panjang).

---

## 4. Eksperimen & Evaluasi (Hasil UTS)

Untuk memenuhi Soal 03, 04, dan 05, evaluasi formal dilakukan menggunakan skrip `eval.py` dan `gold_set.json` (kunci jawaban manual).

* **Model Boolean** dievaluasi menggunakan Precision, Recall, dan F1-Score.
* **Model VSM** dievaluasi menggunakan **Mean Average Precision (MAP@10)** untuk mengukur kualitas ranking.

### 4.1. Hasil Evaluasi Keseluruhan

Tabel berikut menunjukkan hasil eksekusi `eval.py` terhadap 3 kueri *gold set*:

| QID | Model | Metrics | Details |
| :--- | :--- | :--- | :--- |
| q1 | Boolean | P: 0.07, R: 0.89, F1: 0.13 | (Ret: 117, Rel: 9, TP: 8) |
| q1 | VSM (TF-IDF) | AP@10: 0.977 | (Top 3: [344, 343, 96]) |
| q1 | VSM (Sublinear)| AP@10: 0.778 | (Top 3: [343, 344, 15]) |
| q2 | Boolean | P: 0.10, R: 0.86, F1: 0.17 | (Ret: 63, Rel: 7, TP: 6) |
| q2 | VSM (TF-IDF) | AP@10: 0.744 | (Top 3: [82, 53, 93]) |
| q2 | VSM (Sublinear)| AP@10: 0.582 | (Top 3: [95, 2, 187]) |
| q3 | Boolean | P: 0.17, R: 1.00, F1: 0.30 | (Ret: 23, Rel: 4, TP: 4) |
| q3 | VSM (TF-IDF) | AP@10: 0.736 | (Top 3: [343, 330, 344]) |
| q3 | VSM (Sublinear)| AP@10: 0.736 | (Top 3: [343, 330, 344]) |

### 4.2. Perbandingan Skema Bobot VSM (Soal 05)

Perbandingan performa *ranking* antara dua skema pembobotan VSM:

| Skema | Mean Average Precision (MAP@10) |
| :--- | :--- |
| **VSM (TF-IDF Standar)** | **0.8189** |
| VSM (Sublinear TF-IDF) | 0.6985 |

### 4.3. Analisis Hasil
1.  **Model Boolean:** Sesuai dengan hasil evaluasi, Model Boolean menunjukkan **Recall yang sangat tinggi** (rata-rata >0.9), yang berarti ia berhasil menemukan hampir semua dokumen relevan. Namun, **Precision-nya sangat rendah** (rata-rata <0.15), karena ia juga mengembalikan sejumlah besar dokumen tidak relevan (*noise*) dan tidak memiliki kemampuan *ranking*.
2.  **Model VSM:** Model VSM secara signifikan lebih unggul. Berdasarkan perbandingan skema bobot, **skema TF-IDF standar (MAP = 0.8189)** terbukti memberikan performa *ranking* yang lebih baik dan lebih akurat dalam menempatkan dokumen relevan di peringkat teratas dibandingkan dengan skema Sublinear TF-IDF (MAP = 0.6985) pada korpus data ini.

---

## 5. Cara Penggunaan & Replikasi

### Langkah 1: Setup Lingkungan
```bash
# 1. Clone repositori
git clone https://github.com/candrawij/tempat-kemah-web-v2.git
cd tempat-kemah-web-v2

# 2. Buat virtual environment (disarankan)
python -m venv .venv
.venv\Scripts\activate

# 3. Install semua dependensi
pip install -r requirements.txt
```
Langkah 2: Bangun Indeks (Hanya sekali)
Sebelum menjalankan aplikasi, Anda harus membuat file indeks dari korpus.

```bash
python build_index.py
```
(Tunggu hingga selesai dan folder Assets/ terisi).

Langkah 3: Menjalankan Evaluasi (UTS)
Untuk mereplikasi hasil evaluasi di atas.

```bash
python eval.py
```
(Akan menampilkan tabel P/R/F1 dan MAP@10).

Langkah 4: Menjalankan CLI Orchestrator (Soal 05)
Untuk berinteraksi dengan mesin pencari via terminal.

Contoh VSM (default):
```bash
python search.py --model vsm --query "kamar mandi bersih dan murah" --k 3
```

Contoh VSM (Sublinear):
```bash
python search.py --model vsm --weighting sublinear --query "alam sejuk" --k 3
```

Contoh Boolean:
```bash
python search.py --model boolean --query "alam AND sejuk NOT wisata"
```
Langkah 5: Menjalankan Aplikasi Web (Portofolio)
Untuk menjalankan aplikasi web RAG berbasis Streamlit.

```bash
streamlit run streamlit_app.py
```
(Buka http://localhost:8501 di browser Anda).

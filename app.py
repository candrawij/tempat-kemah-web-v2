print("==================================================")
print("MESIN PENCARIAN REKOMENDASI TEMPAT KEMAH VSM SIAP!")
print("==================================================")
print("Anda dapat memasukkan kata kunci untuk mencari rekomendasi.")

while True:
    try:    
        # Mengambil input query dari pengguna
        query_text = input("\nMasukkan kata kunci pencarian (atau ketik 'keluar' untuk berhenti): \n").strip()
        
        if query_text.lower() in ('keluar', 'exit', 'berhenti', 'quit', 'stop', 'kembali'):
            print("\nSesi pencarian diakhiri. Terima kasih!")
            break
        
        if not query_text:
            continue

        start_time = time.time()
            
        # Panggil fungsi pencarian VSM
        vsm_tokens, intent, region = analyze_full_query(query_text)

        # Simpan riwayat pencarian
        log_pencarian(query_text, vsm_tokens, intent, region)
        
        # Panggil fungsi pencarian dengan hasil analisis
        vsm_ranking = search_by_keyword(vsm_tokens, intent, region)

        # Deteksi region untuk ditampilkan
        filter_status = f"Filtered by: {region.upper()}" if region else "No Region Filter Applied"
        intent_status = f"Intent: {intent}" if intent else "Intent: VSM Relevancy"
        
        print("\n--------------------------------------------------")
        print(f"HASIL PENCARIAN untuk: '{query_text}'")
        print(f"Kata Kunci Diproses: {vsm_tokens}")
        print(f"Status Filter: {filter_status}")
        print(f"Mode Pencarian: {intent_status}")
        print("--------------------------------------------------")

        if vsm_ranking:
            if intent == 'RATING_TOP':
                print("Rekomendasi Tempat Kemah (Diurutkan berdasarkan Rating Tertinggi):")
            elif intent == 'RATING_BOTTOM':
                print("Rekomendasi Tempat Kemah (Diurutkan berdasarkan Rating Terendah):")
            else:
                print("Rekomendasi Tempat Kemah (Diurutkan berdasarkan Relevansi Ulasan):")
            
            for i, item in enumerate(vsm_ranking):
                print(f"{i+1}. {item['name']}")
                print(f"   | Lokasi: {item['location']}")
                print(f"   | Rata-rata Rating Tempat: {item['avg_rating']:.2f}")
                print(f"   | Skor Relevansi (VSM Score): {item['top_vsm_score']:.4f}")
            
            # Logika lanjut
            continue_input = input("\nApakah Anda ingin melanjutkan pencarian? (ya/tidak): ").strip().lower()
            
            if continue_input not in ('ya', 'y'):
                print("\nSesi pencarian diakhiri. Terima kasih!")
                break
                
            # Hapus output sebelum loop selanjutnya
            clear_output(wait=True) 
            print("Mesin pencarian siap untuk query selanjutnya...")
        else:
            print("Tidak ditemukan tempat kemah yang relevan dengan kata kunci ini.")
            
            # Logika lanjut
            continue_input = input("\nApakah Anda ingin melanjutkan pencarian? (ya/tidak): ").strip().lower()
            
            if continue_input not in ('ya', 'y'):
                print("\nSesi pencarian diakhiri. Terima kasih!")
                break
                
            # Hapus output sebelum loop selanjutnya
            clear_output(wait=True) 
            print("Mesin pencarian siap untuk query selanjutnya...")

    except KeyboardInterrupt:   
        print("\nSesi pencarian diakhiri oleh pengguna. Terima kasih!")
        break
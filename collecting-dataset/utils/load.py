def store_to_csv(data, file_path):
    """Fungsi untuk menyimpan data ke dalam file CSV."""
    try:
        # Menyimpan data ke file CSV
        data.to_csv(file_path, index=False)
        print(f"Data berhasil disimpan ke {file_path}")
    
    except Exception as e:
        print(f"Terjadi kesalahan saat menyimpan data: {e}")
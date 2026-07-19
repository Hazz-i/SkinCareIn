import os
import re
import glob
import pandas as pd
from utils.database import engine, connect_to_db

def clean_extracted_text(raw_text) -> str:
    """Clean markdown, extra spaces, and newlines from description"""
    if pd.isna(raw_text) or raw_text is None:
        return "Deskripsi tidak tersedia"
    
    raw_text = str(raw_text)
    # Remove bold markdown **text**
    cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', raw_text)
    # Normalize multiple newlines
    cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
    # Replace single newlines with spaces
    cleaned = re.sub(r'\n', ' ', cleaned)
    # Remove bullet points/stars
    cleaned = re.sub(r'\*+', '', cleaned)
    # Remove extra spaces
    cleaned = re.sub(r'\s{2,}', ' ', cleaned)
    
    return cleaned.strip()

def extract_ingredients_section(text) -> str:
    """Extract ingredients section from the description text"""
    if pd.isna(text) or text is None:
        return "Ingredients tidak ditemukan."
    
    text = str(text)
    # Find ingredients section using regex
    pattern = r"(?:Ingredients|Bahan-bahan|Bahan)\s*[::]?\s*(.+)"
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return "Ingredients tidak ditemukan."

def load_and_transform_raw_csvs():
    """Find and combine all raw product CSVs, then transform them"""
    print("Mencari file raw CSV...")
    
    # Paths where raw files might be
    raw_paths = [
        "collecting-dataset/data/raw_data/raw_*.csv",
        "collecting-dataset/data/raw_*.csv",
        "collecting-dataset/raw_*.csv"
    ]
    
    all_files = []
    for path in raw_paths:
        all_files.extend(glob.glob(path))
        
    # Remove duplicates if any
    all_files = list(set(all_files))
    
    if not all_files:
        print("❌ Tidak ditemukan file raw CSV (raw_*.csv) untuk diproses.")
        return None
        
    print(f"Ditemukan {len(all_files)} file raw CSV:")
    for f in all_files:
        print(f" - {f}")
        
    dfs = []
    for f in all_files:
        try:
            df = pd.read_csv(f)
            dfs.append(df)
        except Exception as e:
            print(f"❌ Gagal membaca {f}: {e}")
            
    if not dfs:
        return None
        
    combined_df = pd.concat(dfs, ignore_index=True)
    print(f"Total baris data mentah terbilang: {len(combined_df)}")
    
    # Transform data
    print("Menjalankan pembersihan dan ekstraksi kandungan bahan...")
    combined_df['Description'] = combined_df['Description'].apply(clean_extracted_text)
    combined_df['Ingredients'] = combined_df['Description'].apply(extract_ingredients_section)
    
    return combined_df

def main():
    # 1. Cek koneksi database terlebih dahulu
    print("=== Menghubungkan ke Database ===")
    if not connect_to_db():
        print("❌ Koneksi database gagal. Harap periksa konfigurasi .env Anda.")
        return

    # 2. Cari file CSV hasil proses (processed_data.csv)
    # Jika tidak ada, buat secara otomatis dari file raw
    csv_file = "processed_data.csv"
    if not os.path.exists(csv_file):
        csv_file = "collecting-dataset/processed_data.csv"
        
    if os.path.exists(csv_file):
        print(f"✓ Menemukan file data terproses di: {csv_file}")
        try:
            df = pd.read_csv(csv_file)
        except Exception as e:
            print(f"❌ Gagal membaca {csv_file}: {e}")
            df = None
    else:
        df = None
        
    if df is None:
        print("⚠️ processed_data.csv tidak ditemukan. Mencoba memproses dari raw data...")
        df = load_and_transform_raw_csvs()
        if df is None:
            print("❌ Gagal mendapatkan data untuk diunggah.")
            return
            
        # Simpan processed_data.csv di root
        df.to_csv("processed_data.csv", index=False)
        print("✓ Berhasil menyimpan data terproses ke 'processed_data.csv'")

    # 3. Normalisasi kolom agar sesuai dengan yang dibutuhkan oleh schema (lowercase & snake_case)
    # 'Title' -> 'title', 'Image URL' -> 'image_url', dst.
    df.columns = [col.lower().replace(' ', '_') for col in df.columns]
    
    # 4. Upload ke database (tabel 'products')
    table_name = "products"
    try:
        print(f"\n=== Mengunggah Data ke Database ===")
        print(f"Mengunggah {len(df)} produk ke tabel '{table_name}'...")
        
        # Simpan ke SQL
        df.to_sql(table_name, con=engine, if_exists='replace', index=False)
        print(f"✓ Berhasil mengunggah data! Tabel '{table_name}' siap digunakan.")
        
        # Jalankan test query sederhana
        with engine.connect() as conn:
            # Import text from sqlalchemy for raw SQL text execution in sqlalchemy 2.0+
            from sqlalchemy import text
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            count = result.scalar()
            print(f"✓ Verifikasi database: Ada {count} baris di tabel '{table_name}'.")
            
    except Exception as e:
        print(f"❌ Terjadi kesalahan saat menulis ke database: {e}")

if __name__ == "__main__":
    main()

import pandas as pd
import glob

import os
import re

def clean_extracted_text(raw_text) -> str:
    """
    Membersihkan teks hasil ekstraksi OCR atau AI dari karakter khusus dan formatting markdown.

    Langkah pembersihan:
    - Hilangkan markdown (e.g., **bold**)
    - Ganti newline ganda menjadi paragraf
    - Ganti newline tunggal menjadi spasi
    - Hilangkan karakter aneh (*, multiple space, dsb.)
    - Strip spasi awal/akhir

    Args:
        raw_text: Teks asli hasil ekstraksi AI (bisa string atau None/NaN)

    Returns:
        str: Teks yang sudah bersih
    """
    # Handle non-string values (NaN, None, etc.)
    if pd.isna(raw_text) or raw_text is None:
        return "Deskripsi tidak tersedia"
    
    # Convert to string if not already
    raw_text = str(raw_text)
    
    # Hapus markdown tebal seperti **text**
    cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', raw_text)

    # Ganti newline ganda dengan pemisah paragraf
    cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)

    # Ganti newline tunggal dengan spasi
    cleaned = re.sub(r'\n', ' ', cleaned)

    # Hapus bullet atau bintang tidak penting
    cleaned = re.sub(r'\*+', '', cleaned)

    # Hilangkan spasi berlebih
    cleaned = re.sub(r'\s{2,}', ' ', cleaned)

    # Strip spasi awal dan akhir
    return cleaned.strip()

def extract_ingredients_section(text) -> str:
    """
    Mengekstrak hanya bagian Ingredients/Bahan dari teks panjang.

    Akan mencari kata 'Ingredients' atau 'Bahan' dan mengambil teks setelahnya,
    sampai akhir kalimat atau titik terakhir (jika tidak ada penanda khusus).
    """
    # Handle non-string values (NaN, None, etc.)
    if pd.isna(text) or text is None:
        return "Ingredients tidak ditemukan."
    
    # Convert to string if not already
    text = str(text)
    
    pattern = r"(?:Ingredients|Bahan-bahan|Bahan)\s*[::]?\s*(.+)"
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return "Ingredients tidak ditemukan."

def transform_all_data(input_folder='data'):
    all_files = glob.glob(os.path.join(input_folder, "raw_*.csv"))

    combined_df = pd.concat([pd.read_csv(f) for f in all_files], ignore_index=True)
    
    combined_df['Description'] = combined_df['Description'].apply(clean_extracted_text)
    combined_df['Ingredients'] = combined_df['Description'].apply(extract_ingredients_section)

    # Drop baris kosong
    # combined_df = combined_df.dropna(subset=['Title', 'Price'])
    return combined_df
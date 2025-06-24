from fastapi import HTTPException
import requests
import base64
import re

# Fungsi untuk mengambil gambar dari URL
def get_image_from_url(image_url: str) -> bytes:
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        return response.content
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gagal mengambil gambar dari URL: {str(e)}")

# Fungsi untuk mengambil gambar dari path lokal
def get_image_from_path(image_path: str) -> bytes:
    try:
        with open(image_path, "rb") as f:
            return f.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gagal membaca gambar dari path lokal: {str(e)}")
    
def convert_image_to_base64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")

# Fungsi untuk ekstraksi teks menggunakan Gemini
def extract_text_from_image(image_bytes: bytes, client) -> str:
    try:
        base64_image = convert_image_to_base64(image_bytes)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                {
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": base64_image,
                    }
                },
                "baca teks yang ada dalam gambar ini"
            ],
        )
        return response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error dari Gemini API: {str(e)}")

def clean_extracted_text(raw_text: str) -> str:
    """
    Membersihkan teks hasil ekstraksi OCR atau AI dari karakter khusus dan formatting markdown.

    Langkah pembersihan:
    - Hilangkan markdown (e.g., **bold**)
    - Ganti newline ganda menjadi paragraf
    - Ganti newline tunggal menjadi spasi
    - Hilangkan karakter aneh (*, multiple space, dsb.)
    - Strip spasi awal/akhir

    Args:
        raw_text (str): Teks asli hasil ekstraksi AI

    Returns:
        str: Teks yang sudah bersih
    """
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

import re

def extract_ingredients_section(text: str) -> str:
    """
    Mengekstrak hanya bagian Ingredients/Bahan dari teks panjang.

    Akan mencari kata 'Ingredients' atau 'Bahan' dan mengambil teks setelahnya,
    sampai akhir kalimat atau titik terakhir (jika tidak ada penanda khusus).
    """
    pattern = r"(?:Ingredients|Bahan-bahan|Bahan)\s*[:：]?\s*(.+)"
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return "Ingredients tidak ditemukan."
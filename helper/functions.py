from fastapi import HTTPException
import requests
import base64
import json
import re
from enum import Enum
import torch
import torch.nn as nn
from torchvision.models import resnet50, ResNet50_Weights
from torchvision import transforms
from PIL import Image
from io import BytesIO

from helper.ingredients import ingredients_avoid_oily, ingredients_avoid_dry, ingredients_avoid_normal, ingredients_avoid_acne, ingredients_avoid_sensitive

class SkinType(str, Enum):
    oily = "oily"
    dry = "dry"
    normal = "normal"
    acne = "acne"
    sensitive = "sensitive"

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

# funsi untuk membersihkan teks hasil ekstraksi OCR atau AI
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


# fungsi untuk mengekstrak bagian Ingredients/Bahan dari teks panjang
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

# fungsi untuk mendapatkan daftar bahan yang harus dihindari berdasarkan jenis kulit
def load_ingredients_details():
    """Load ingredients details from JSON file"""
    try:
        with open('utils/details.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# fing harmful ingredients based on skin type
ingredients_details = load_ingredients_details()
def find_harmful_ingredients_with_details(extracted_ingredients: str, avoid_list: list, skin_type: str) -> list:
    """Find harmful ingredients from extracted text with detailed explanations"""
    harmful_found = []
    extracted_lower = extracted_ingredients.lower()
    
    # Map skin type to details key
    skin_type_key_map = {
        "oily": "oily",
        "dry": "dry", 
        "normal": "normal",
        "acne": "acne_prone",
        "sensitive": "sensitive"
    }
    
    details_key = skin_type_key_map.get(skin_type, skin_type)
    skin_details = ingredients_details.get(details_key, {})
    
    for ingredient in avoid_list:
        if ingredient.lower() in extracted_lower:
            ingredient_detail = {
                "name": ingredient,
                "reason": skin_details.get(ingredient, "Tidak cocok untuk jenis kulit ini berdasarkan penelitian dermatologis.")
            }
            harmful_found.append(ingredient_detail)
    
    return harmful_found

def parse_ingredients_to_list(ingredients_text: str) -> list:
    """Parse ingredients text into a clean list, handling special cases like '1,2-hexanediol'"""
    if not ingredients_text:
        return []
    
    # First, protect chemical compounds with numbers and commas (like 1,2-hexanediol)
    # Replace pattern like "number,number-" with "number.number-"
    protected_text = re.sub(r'(\d+),(\d+)-', r'\1.\2-', ingredients_text)
    
    # Split by comma and clean each ingredient
    ingredients_list = [
        ingredient.strip().title() 
        for ingredient in protected_text.split(',')
        if ingredient.strip()
    ]
    
    # Remove size/volume information from last ingredient if present
    if ingredients_list:
        last_ingredient = ingredients_list[-1]
        # Remove patterns like "30 ml/1.76 fl.oz"
        cleaned_last = re.sub(r'\s*\d+.*?(?:ml|oz|g|kg|fl\.oz).*$', '', last_ingredient, flags=re.IGNORECASE)
        if cleaned_last.strip():
            ingredients_list[-1] = cleaned_last.strip()
        else:
            ingredients_list.pop()  # Remove if nothing left after cleaning
    
    return ingredients_list

def get_ingredients_to_avoid(skin_type: SkinType) -> list:
    """Get list of ingredients to avoid based on skin type"""
    skin_type_map = {
        SkinType.oily: ingredients_avoid_oily,
        SkinType.dry: ingredients_avoid_dry,
        SkinType.normal: ingredients_avoid_normal,
        SkinType.acne: ingredients_avoid_acne,
        SkinType.sensitive: ingredients_avoid_sensitive
    }
    return skin_type_map.get(skin_type, [])

# Load the pre-trained ResNet50 model + higher level layers
def load_skin_type_model():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = resnet50(weights=ResNet50_Weights.DEFAULT).to(device)
    model.eval()
    
    # Remove the final fully connected layer (classifier)
    model = nn.Sequential(*(list(model.children())[:-1]))
    
    return model

# Predict skin type based on image
def predict_skin_type(image_bytes: bytes, model, transform) -> str:
    """
    Predict skin type from image bytes.

    Args:
        image_bytes (bytes): Image data in bytes
        model: The skin type prediction model
        transform: The transformation pipeline for the input image

    Returns:
        str: Predicted skin type
    """
    try:
        # Convert bytes to PIL Image
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        
        # Apply the transformations
        image_tensor = transform(image).unsqueeze(0)
        
        # Forward pass through the model
        with torch.no_grad():
            output = model(image_tensor)
        
        # The output is a feature vector; in a real scenario, you would have a mapping
        # from these features to skin types based on your training data.
        # For demonstration, let's assume a dummy mapping:
        skin_types = ["oily", "dry", "normal", "acne", "sensitive"]
        _, predicted_idx = torch.max(output, 1)
        return skin_types[predicted_idx.item()]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in skin type prediction: {str(e)}")

# Define the image transformation pipeline
image_transform = transforms.Compose([
    transforms.Resize((224, 224)),  # Resize to 224x224 pixels
    transforms.ToTensor(),          # Convert image to tensor
    transforms.Normalize(           # Normalize with ImageNet stats
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    ),
])

def load_resnet_skin_classifier():
    """
    Load ResNet50 model for skin type classification from Hugging Face Hub
    
    Returns:
        tuple: (model, transform) - The loaded model and preprocessing transform
    """
    try:
        # === Load model dari Hugging Face Hub ===
        model = resnet50(weights=None)
        model.fc = nn.Linear(2048, 3)  # 3 classes: dry, normal, oily

        # Load dari URL Hugging Face (model yang sudah diupload ulang)
        state_dict = torch.hub.load_state_dict_from_url(
            "https://huggingface.co/Raveem/SkinSight/resolve/main/pytorch_model.bin",
            map_location="cpu"
        )
        model.load_state_dict(state_dict)
        model.eval()
        
        # Define preprocessing transform
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406],
                                [0.229, 0.224, 0.225])
        ])
        
        return model, transform
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading model from Hugging Face: {str(e)}")

def get_skin_type_label_mapping():
    """
    Get the label mapping for skin type classification
    
    Returns:
        dict: Index to label mapping
    """
    return {0: "dry", 1: "normal", 2: "oily"}

def predict_skin_type_from_image(image_bytes: bytes, model, transform, index_label: dict):
    """
    Predict skin type from image bytes using trained ResNet model
    
    Args:
        image_bytes (bytes): Image data in bytes
        model: The trained ResNet model
        transform: Preprocessing transform
        index_label (dict): Index to label mapping
        
    Returns:
        dict: Prediction results with probabilities and predicted label
    """
    try:
        # Convert bytes to PIL Image and preprocess
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        img_tensor = transform(image).unsqueeze(0).to('cpu')

        # Make prediction
        with torch.no_grad():
            output = model(img_tensor)
            probs = torch.nn.functional.softmax(output, dim=1)[0]

        # Format hasil ke bentuk {label: percent}
        result = {
            index_label[i]: round(probs[i].item() * 100, 2)
            for i in range(len(probs))
        }

        # Tambahkan prediksi tertinggi
        pred_idx = torch.argmax(probs).item()
        result["predicted_label"] = index_label[pred_idx]

        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in skin type prediction: {str(e)}")
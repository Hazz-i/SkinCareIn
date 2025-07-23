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
import cv2
import numpy as np
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
                "cari ingredients/bahan/komposisi dalam gambar ini dan berikan hasilnya dalam format teks biasa tanpa markdown atau formatting lainnya. buang teks yang tidak relevan seperti nama brand, nama produk, atau informasi lain yang tidak berkaitan dengan bahan, serta jika tidak terdapat ingredients sama sekali, tampilkan ingredients not found.",
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

def enhanced_face_detection(image_bytes):
    """
    Enhanced face detection with multiple validations and human face verification
    
    Args:
        image_bytes: Byte data of the image
        
    Returns:
        dict: Detection results with various validations
    """
    try:
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return {
                "has_face": False,
                "reason": "Image cannot be read or format is not supported",
                "face_count": 0,
                "is_clear": False,
                "confidence": 0.0,
                "face_area_percentage": 0.0
            }
        
        # Get image dimensions
        height, width = img.shape[:2]
        total_area = height * width
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Load multiple cascade classifiers for better detection
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        profile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')
        eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        
        # Detect frontal faces with multiple scales
        frontal_faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.05,
            minNeighbors=6,
            minSize=(80, 80),
            maxSize=(int(width*0.8), int(height*0.8)),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # Detect profile faces if no frontal faces found
        profile_faces = []
        if len(frontal_faces) == 0:
            profile_faces = profile_cascade.detectMultiScale(
                gray,
                scaleFactor=1.05,
                minNeighbors=5,
                minSize=(80, 80),
                maxSize=(int(width*0.8), int(height*0.8))
            )
        
        # Combine and filter overlapping faces
        all_faces = list(frontal_faces) + list(profile_faces)
        filtered_faces = []
        
        # Remove overlapping detections
        for face in all_faces:
            x, y, w, h = face
            is_duplicate = False
            for existing in filtered_faces:
                ex, ey, ew, eh = existing
                # Check if faces overlap significantly
                overlap_x = max(0, min(x + w, ex + ew) - max(x, ex))
                overlap_y = max(0, min(y + h, ey + eh) - max(y, ey))
                overlap_area = overlap_x * overlap_y
                face_area = w * h
                
                if overlap_area > 0.3 * face_area:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered_faces.append(face)
        
        face_count = len(filtered_faces)
        
        if face_count == 0:
            return {
                "has_face": False,
                "reason": "No human face detected in the image",
                "face_count": 0,
                "is_clear": False,
                "confidence": 0.0,
                "face_area_percentage": 0.0
            }
        
        # Get the largest face (assuming it's the main subject)
        largest_face = max(filtered_faces, key=lambda face: face[2] * face[3])
        x, y, w, h = largest_face
        
        # Extract face region for additional validations
        face_roi = gray[y:y+h, x:x+w]
        face_roi_color = img[y:y+h, x:x+w]
        
        # Validate face using eye detection (human faces should have eyes)
        eyes = eye_cascade.detectMultiScale(
            face_roi,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(10, 10)
        )
        
        has_eyes = len(eyes) >= 1  # At least one eye should be visible
        
        if not has_eyes:
            return {
                "has_face": False,
                "reason": "Detected region does not appear to be a human face (no eyes detected)",
                "face_count": face_count,
                "is_clear": False,
                "confidence": 0.0,
                "face_area_percentage": 0.0
            }
        
        # Calculate face area percentage
        face_area = w * h
        face_area_percentage = (face_area / total_area) * 100
        
        # Validate face size (should be at least 8% of image for good quality)
        min_face_area_percentage = 8.0
        min_face_dimension = 120
        
        # Check image sharpness using Laplacian variance
        laplacian_var = cv2.Laplacian(face_roi, cv2.CV_64F).var()
        
        # Check if face has sufficient contrast
        mean_intensity = np.mean(face_roi)
        std_intensity = np.std(face_roi)
        has_contrast = std_intensity > 20 and 30 < mean_intensity < 220
        
        # Overall clarity check
        is_clear = (
            face_area_percentage >= min_face_area_percentage and 
            min(w, h) >= min_face_dimension and 
            has_contrast
        )
        
        # Calculate confidence based on multiple factors
        size_score = min(face_area_percentage / 25.0, 1.0)
        contrast_score = min(std_intensity / 50.0, 1.0)
        eye_score = min(len(eyes) / 2.0, 1.0)
        
        confidence = (size_score  + contrast_score + eye_score) / 4.0
        
        # Additional validation messages
        if not is_clear:
            if face_area_percentage < min_face_area_percentage:
                reason = f"Face is too small in the image ({face_area_percentage:.1f}% of image area). Please use a closer photo."
            elif not has_contrast:
                reason = "Image has poor lighting or contrast. Please use better lighting."
            else:
                reason = "Face quality is insufficient for analysis."
                
            return {
                "has_face": True,
                "reason": reason,
                "face_count": face_count,
                "is_clear": False,
                "confidence": confidence,
                "face_area_percentage": face_area_percentage
            }
        
        return {
            "has_face": True,
            "reason": "Human face successfully detected and validated",
            "face_count": face_count,
            "is_clear": is_clear,
            "confidence": confidence,
            "face_area_percentage": face_area_percentage,
            "quality_metrics": {
                "sharpness": laplacian_var,
                "contrast": std_intensity,
                "eyes_detected": len(eyes),
                "face_size": f"{w}x{h}"
            }
        }
        
    except Exception as e:
        return {
            "has_face": False,
            "reason": f"Error in face detection: {str(e)}",
            "face_count": 0,
            "is_clear": False,
            "confidence": 0.0,
            "face_area_percentage": 0.0
        }

def detect_face_in_image(image_bytes):
    """
    Simplified face detection for backward compatibility
    Returns True only if a clear human face is detected
    """
    result = enhanced_face_detection(image_bytes)
    return result["has_face"] and result["is_clear"]

# BeautifulSoup and requests setup
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
    )
}

def fetching_content(url):
    """Mengambil konten HTML dari URL yang diberikan."""
    session = requests.Session()
    
    try:
        response = session.get(url, headers=HEADERS)
        response.raise_for_status()  # Raise an exception for 4xx/5xx responses
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Terjadi kesalahan ketika melakukan requests terhadap {url}: {e}")
        return None
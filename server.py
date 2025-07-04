from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from google import genai
from enum import Enum
import os

from helper import (
    get_image_from_url, get_image_from_path, extract_text_from_image, 
    clean_extracted_text, extract_ingredients_section, find_harmful_ingredients_with_details, 
    parse_ingredients_to_list, get_ingredients_to_avoid, load_resnet_skin_classifier, 
    get_skin_type_label_mapping, predict_skin_type_from_image
)

load_dotenv()

app = FastAPI(title="SkinSight API", 
                description="API for skincare recommendations",
                version="1.0.0")

class SkinType(str, Enum):
    oily = "oily"
    dry = "dry"
    normal = "normal"
    acne = "acne"
    sensitive = "sensitive"

class ScanIngredientsRequest(BaseModel):
    image_url: str | None = None
    image_path: str | None = None
    skin_type: SkinType

class PredictRequest(BaseModel):
    image_url: str | None = None
    image_path: str | None = None
    
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Load model and preprocessing transform
model, transform = load_resnet_skin_classifier()

# Label Mapping
index_label = get_skin_type_label_mapping()

@app.get("/")
def index():
    return {"message": "Developernya ganteng banget?"}

# === Read Ingredients Endpoint ===
@app.post("/read-ingredients", response_model=dict)
async def read_ingredients(
    data: ScanIngredientsRequest = Body(...)
):
    """
    Scan skincare product image and analyze ingredients based on skin type
    
    Parameters:
        - image_url/image_path: URL or path to product image 
        - skin_type: User's skin type (oily, dry, normal, acne, sensitive)
        
    Returns:
        - Detected ingredients as list
        - List of ingredients to avoid for skin type
        - List of harmful ingredients found with detailed reasons
        - Skin safety recommendation
    """
    try:
        if not data.image_url and not data.image_path:
            raise HTTPException(status_code=400, detail="Image URL atau path diperlukan.")
        
        # Extract text from image
        image_bytes = get_image_from_url(data.image_url) if data.image_url else get_image_from_path(data.image_path)
        extracted_text = extract_text_from_image(image_bytes, client)
        
        if not extracted_text:
            raise HTTPException(status_code=404, detail="Tidak ada teks yang ditemukan dalam gambar.")
        
        # Clean and extract ingredients section
        extracted_text = clean_extracted_text(extracted_text)
        ingredients_text = extract_ingredients_section(extracted_text)
        
        # Parse ingredients into list
        ingredients_list = parse_ingredients_to_list(ingredients_text)
        
        # Get ingredients to avoid based on skin type
        avoid_list = get_ingredients_to_avoid(data.skin_type)
        
        # Find harmful ingredients with detailed explanations
        harmful_ingredients = find_harmful_ingredients_with_details(ingredients_text, avoid_list, data.skin_type.value)
        
        # Create recommendation
        is_safe = len(harmful_ingredients) == 0
        
        
        return {
            "extracted_ingredients": ingredients_list,
            "harmful_ingredients_found": harmful_ingredients,
            "is_safe": is_safe,
            "total_harmful_ingredients": len(harmful_ingredients),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")
    
# === Predict Endpoint ===
@app.post("/predict")
async def predict(data: PredictRequest = Body(...)):
    try:
        if not data.image_url and not data.image_path:
            raise HTTPException(status_code=400, detail="Image URL atau path diperlukan.")
        
        # Get image from URL or path
        image_bytes = get_image_from_url(data.image_url) if data.image_url else get_image_from_path(data.image_path)
        
        # Predict skin type using helper function
        result = predict_skin_type_from_image(image_bytes, model, transform, index_label)

        return JSONResponse(result)

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
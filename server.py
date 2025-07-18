from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Body, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from helper.news import get_news, get_news_list
from pydantic import BaseModel
from google import genai
from enum import Enum
import os
import io

from helper import (
    get_image_from_url, extract_text_from_image, 
    clean_extracted_text, extract_ingredients_section, find_harmful_ingredients_with_details, 
    parse_ingredients_to_list, get_ingredients_to_avoid, load_resnet_skin_classifier, 
    get_skin_type_label_mapping, predict_skin_type_from_image, enhanced_face_detection
)

from helper.recommendations import get_skincare_recommendations

load_dotenv()

app = FastAPI(title="SkinSight API", 
                description="API for skincare recommendations",
                version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("CORS_ORIGIN"),
        "http://localhost:3000", 
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class SkinType(str, Enum):
    oily = "oily"
    dry = "dry"
    normal = "normal"
    acne = "acne"
    sensitive = "sensitive"

class ScanIngredientsRequest(BaseModel):
    image_url: str | None = None
    skin_type: SkinType

class PredictRequest(BaseModel):
    image_url: str | None = None
    
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
    file: UploadFile = File(None),
    image_url: str = Form(None),
    skin_type: str = Form(...)
):
    """
    Scan skincare product image and analyze ingredients based on skin type
    
    Parameters:
        - file: Uploaded image file
        - image_url: URL to product image (alternative to file)
        - skin_type: User's skin type (oily, dry, normal, acne, sensitive)
        
    Returns:
        - Detected ingredients as list
        - List of ingredients to avoid for skin type
        - List of harmful ingredients found with detailed reasons
        - Skin safety recommendation
        - Content-based product recommendations (simplified)
    """
    try:
        if not file and not image_url:
            raise HTTPException(status_code=400, detail="File gambar atau URL gambar diperlukan.")
        
        # Validate skin_type
        valid_skin_types = ["oily", "dry", "normal", "acne", "sensitive"]
        if skin_type not in valid_skin_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Skin type tidak valid. Pilihan yang tersedia: {', '.join(valid_skin_types)}"
            )
        
        # Extract text from image
        if file:
            # Read uploaded file as bytes
            file_content = await file.read()
            # Pass bytes directly, not BytesIO
            extracted_text = extract_text_from_image(file_content, client)
        else:   
            # Get image from URL
            image_bytes = get_image_from_url(image_url)
            extracted_text = extract_text_from_image(image_bytes, client)
            
        if not extracted_text:
            raise HTTPException(status_code=404, detail="Tidak ada teks yang ditemukan dalam gambar.")
        
        # Clean and extract ingredients section
        extracted_text = clean_extracted_text(extracted_text)
        ingredients_text = extract_ingredients_section(extracted_text)
        
        # Parse ingredients into list
        ingredients_list = parse_ingredients_to_list(ingredients_text)
        
        # Get ingredients to avoid based on skin type
        avoid_list = get_ingredients_to_avoid(skin_type)
        
        # Find harmful ingredients with detailed explanations
        harmful_ingredients = find_harmful_ingredients_with_details(ingredients_text, avoid_list, skin_type)
        
        # Create recommendation
        is_safe = len(harmful_ingredients) == 0
        
        # Get content-based recommendations
        try:
            # Get recommendations based on detected ingredients
            full_recommendations = get_skincare_recommendations(
                input_ingredients=ingredients_list,
                skin_type=skin_type,
                top_k=5
            )
            
            # Simplify recommendations to only include product_name and similarity_score
            simplified_recommendations = []
            for rec in full_recommendations.get('recommendations', []):
                simplified_recommendations.append({
                    'product_name': rec.get('product_name', 'Unknown'),
                    'product_image': rec.get('product_image', 'Unknown'),
                    'product_link': rec.get('product_link', 'Unknown'),
                    'price': rec.get('price', 'Unknown'),
                    'similarity_score': rec.get('similarity_score', 0.0)
                })
            
            recommendations_result = {
                'products': simplified_recommendations,
                'recommendation_count': len(simplified_recommendations)
            }
            
        except Exception as rec_error:
            print(f"Recommendation error: {rec_error}")
            recommendations_result = {
                'recommendations': [],
                'total_found': 0,
                'total_safe': 0,
                'recommendation_count': 0,
                'error': str(rec_error)
            }
        
        return {
            "extracted_ingredients": ingredients_list,
            "harmful_ingredients_found": harmful_ingredients,
            "is_safe": is_safe,
            "total_harmful_ingredients": len(harmful_ingredients),
            "recommendations": recommendations_result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

# === New endpoint for getting recommendations only ===
@app.post("/get-recommendations")
async def get_recommendations_only(
    skin_type: str = Body(...),
    top_k: int = Body(default=10)
):
    """
    Get skincare product recommendations based on skin type from product descriptions
    
    Parameters:
        - skin_type: User's skin type
        - top_k: Number of recommendations to return
        
    Returns:
        - Products suitable for the specified skin type
    """
    try:
        # Validate skin_type
        valid_skin_types = ["oily", "dry", "normal", "acne", "sensitive"]
        if skin_type not in valid_skin_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Skin type tidak valid. Pilihan yang tersedia: {', '.join(valid_skin_types)}"
            )
        
        # Get recommendations based on skin type
        from helper.recommendations import get_skin_type_recommendations
        recommendations = get_skin_type_recommendations(
            skin_type,
            max(1, min(top_k, 20))
        )
        
        return {
            'recommendations': recommendations.get('recommendations', []),
            'total_found': recommendations.get('total_found', 0),
            'skin_type': skin_type,
            'recommendation_count': recommendations.get('recommendation_count', 0)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")

# === Predict Endpoint ===
@app.post("/predict-skin")
async def predict(
    file: UploadFile = File(None),
    image_url: str = Form(None)
):
    try:
        if not file and not image_url:
            raise HTTPException(
                status_code=400, 
                detail="File gambar atau URL gambar diperlukan."
            )
        
        image_bytes = None
        
        # Get image from file or URL with validation
        if file:
            # Validate file type
            if not file.content_type.startswith("image/"):
                raise HTTPException(
                    status_code=400,
                    detail="File yang diupload harus berupa gambar (JPEG, PNG, dll)."
                )
            
            # Validate file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise HTTPException(
                    status_code=400,
                    detail="Ukuran file terlalu besar. Maksimal 10MB."
                )
            
            # Read uploaded file as bytes
            image_bytes = await file.read()
            
            # Validate if file is readable image
            if not image_bytes:
                raise HTTPException(
                    status_code=400,
                    detail="File gambar tidak dapat dibaca atau rusak."
                )
                
        else:
            try:
                # Get image from URL with timeout and validation
                image_bytes = get_image_from_url(image_url)
                if not image_bytes:
                    raise HTTPException(
                        status_code=400,
                        detail="URL gambar tidak dapat diakses atau tidak valid."
                    )
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Gagal mengambil gambar dari URL: {str(e)}"
                )
        
        # Enhanced face detection with multiple validations
        face_detection_result = enhanced_face_detection(image_bytes)
        
        if not face_detection_result["has_face"]:
            raise HTTPException(
                status_code=400,
                detail=f"Face detection failed: {face_detection_result['reason']}. "
                        "Please ensure the image contains a clear human face facing the camera."
            )
        
        # Additional validation for face quality
        if face_detection_result["face_count"] > 1:
            raise HTTPException(
                status_code=400,
                detail="Multiple faces detected in the image. "
                        "Please use a photo with only one face."
            )
        
        # Validate face size and clarity
        if not face_detection_result["is_clear"]:
            raise HTTPException(
                status_code=400,
                detail=f"Face quality insufficient: {face_detection_result['reason']}"
            )
        
        # Pass bytes directly for skin type prediction
        result = predict_skin_type_from_image(image_bytes, model, transform, index_label)
        
        return JSONResponse(result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Terjadi kesalahan dalam memproses gambar: {str(e)}"
        )
        
@app.post("/skincare-news")
async def skincare_news(request: dict = Body(...)):
    """Get skincare news articles"""
    
    try:
        page = request.get("page", 1)
        news = get_news_list(page=page)
        return JSONResponse(news)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/skincare-news-details")
async def skincare_news_detail(request: dict = Body(...)):
    """Get detailed skincare news article by link"""

    try:
        article_link = request.get("article_link")
        if not article_link:
            raise HTTPException(status_code=400, detail="article_link is required")
        
        news = get_news(article_link)
        return JSONResponse(news)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
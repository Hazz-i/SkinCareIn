from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Body, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from helper.educations import get_educations_details, get_educations_list
from helper.news import get_news, get_news_list
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from google import genai
from enum import Enum
import os

from helper import (
    get_image_from_url, extract_text_from_image, 
    clean_extracted_text, extract_ingredients_section, find_harmful_ingredients_with_details, 
    parse_ingredients_to_list, get_ingredients_to_avoid, load_resnet_skin_classifier, 
    get_skin_type_label_mapping, predict_skin_type_from_image
)

from helper.recommendations import get_skincare_recommendations

load_dotenv()

app = FastAPI(
    title="SkinSight API", 
    description="API for skincare recommendations",
    version="1.0.0"
)

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


# =====================================================================
# REQUEST & RESPONSE MODELS FOR API DOCUMENTATION
# =====================================================================

class ProductRecommendation(BaseModel):
    product_name: str = Field(..., description="Nama produk rekomendasi")
    product_image: str = Field(..., description="URL gambar produk")
    product_link: str = Field(..., description="Link produk/sumber")
    price: str = Field(..., description="Harga produk")
    similarity_score: float = Field(..., description="Skor kemiripan formula produk")

class HarmfulIngredientDetail(BaseModel):
    name: str = Field(..., description="Nama bahan berbahaya")
    reason: str = Field(..., description="Alasan mengapa berbahaya untuk tipe kulit tertentu")

class ReadIngredientsRecommendations(BaseModel):
    products: List[ProductRecommendation] = Field(default=[], description="Daftar rekomendasi produk yang aman")
    recommendation_count: int = Field(default=0, description="Jumlah produk rekomendasi")

class ReadIngredientsResponse(BaseModel):
    extracted_ingredients: List[str] = Field(..., description="Daftar kandungan bahan yang berhasil diekstrak")
    harmful_ingredients_found: List[HarmfulIngredientDetail] = Field(..., description="Detail bahan berbahaya yang ditemukan")
    is_safe: bool = Field(..., description="Apakah produk aman untuk tipe kulit yang dipilih")
    total_harmful_ingredients: int = Field(..., description="Total bahan berbahaya yang ditemukan")
    recommendations: ReadIngredientsRecommendations = Field(..., description="Rekomendasi produk dengan kandungan serupa yang aman")

class RecommendationsRequest(BaseModel):
    skin_type: SkinType = Field(..., description="Tipe kulit user")
    top_k: int = Field(default=10, ge=1, le=20, description="Jumlah rekomendasi yang ingin ditampilkan (1-20)")

class SkinTypeRecommendation(BaseModel):
    product_name: str = Field(..., description="Nama produk")
    product_image: str = Field(..., description="URL gambar produk")
    product_link: str = Field(..., description="Link produk/sumber")
    price: str = Field(..., description="Harga produk")
    match_reason: str = Field(..., description="Alasan produk ini cocok")

class RecommendationsResponse(BaseModel):
    recommendations: List[SkinTypeRecommendation] = Field(..., description="Daftar rekomendasi berdasarkan tipe kulit")
    total_found: int = Field(..., description="Total rekomendasi yang ditemukan")
    skin_type: SkinType = Field(..., description="Tipe kulit")
    recommendation_count: int = Field(..., description="Jumlah rekomendasi yang dikembalikan")

class PredictSkinResponse(BaseModel):
    dry: float = Field(..., description="Persentase probabilitas tipe kulit kering")
    normal: float = Field(..., description="Persentase probabilitas tipe kulit normal")
    oily: float = Field(..., description="Persentase probabilitas tipe kulit berminyak")
    predicted_label: str = Field(..., description="Prediksi tipe kulit tertinggi (dry, normal, atau oily)")

class NewsRequest(BaseModel):
    page: int = Field(default=1, description="Nomor halaman berita")

class NewsArticle(BaseModel):
    Title: str = Field(..., description="Judul berita")
    Link: str = Field(..., description="Link berita lengkap")
    Image: str = Field(..., description="URL gambar berita")
    Date: str = Field(..., description="Tanggal publikasi berita (YYYY-MM-DD)")
    Category: str = Field(..., description="Kategori berita")

class NewsPagination(BaseModel):
    Current_Page: str = Field(..., description="Halaman saat ini")
    First_Page: Optional[str] = Field(None, description="Halaman pertama")
    Prev_Page: Optional[str] = Field(None, description="Halaman sebelumnya")
    Next_Page: Optional[str] = Field(None, description="Halaman berikutnya")
    Last_Page: Optional[str] = Field(None, description="Halaman terakhir")

class NewsResponse(BaseModel):
    Article_List: List[NewsArticle] = Field(..., description="Daftar artikel berita")
    Pagination: NewsPagination = Field(..., description="Informasi paginasi berita")

class NewsDetailRequest(BaseModel):
    article_link: str = Field(..., description="URL lengkap berita yang ingin diambil detailnya")

class NewsDetailResponse(BaseModel):
    Title: str = Field(..., description="Judul berita")
    Cover_Image: str = Field(..., description="URL gambar cover berita")
    Date: str = Field(..., description="Tanggal publikasi berita")
    Source: str = Field(..., description="Sumber media berita")
    Author: str = Field(..., description="Penulis berita")
    Content: str = Field(..., description="Isi artikel berita dalam format Markdown")

class EducationsRequest(BaseModel):
    page: int = Field(default=1, description="Nomor halaman edukasi")
    link: str = Field(default="https://www.eduskincare.eu.org/", description="URL dasar scraping edukasi")
    prev_link: Optional[str] = Field(None, description="Link sebelumnya untuk paginasi")

class EducationArticle(BaseModel):
    Title: str = Field(..., description="Judul edukasi")
    Link: str = Field(..., description="Link artikel edukasi")
    Image: str = Field(..., description="URL gambar artikel")
    Snippet: str = Field(..., description="Cuplikan singkat isi artikel")
    Date: str = Field(..., description="Tanggal publikasi (YYYY-MM-DD)")
    Category: str = Field(..., description="Kategori artikel")

class EducationPagination(BaseModel):
    Current_Page: str = Field(..., description="Halaman saat ini")
    First_Page: Optional[str] = Field(None, description="Halaman pertama")
    Prev_Page: Optional[str] = Field(None, description="Halaman sebelumnya")
    Next_Page: Optional[str] = Field(None, description="Halaman berikutnya")
    Last_Page: Optional[str] = Field(None, description="Halaman terakhir")
    Current_Link: str = Field(..., description="Link halaman saat ini")

class EducationsResponse(BaseModel):
    Educations_List: List[EducationArticle] = Field(..., description="Daftar artikel edukasi")
    Pagination: EducationPagination = Field(..., description="Informasi paginasi edukasi")

class EducationDetailRequest(BaseModel):
    article_link: str = Field(..., description="URL lengkap artikel edukasi yang ingin diambil detailnya")

class EducationDetailResponse(BaseModel):
    Title: str = Field(..., description="Judul edukasi")
    Author: str = Field(..., description="Penulis artikel")
    Date: str = Field(..., description="Tanggal publikasi")
    Cover_Image: str = Field(..., description="URL gambar cover")
    Content: str = Field(..., description="Isi artikel edukasi dalam format Markdown")


# =====================================================================
# API CONFIGURATION & SETUP
# =====================================================================

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Load model and preprocessing transform
model, transform = load_resnet_skin_classifier()

# Label Mapping
index_label = get_skin_type_label_mapping()


@app.get("/")
def index():
    return {"message": "Developernya ganteng banget?"}


# === Read Ingredients Endpoint ===
@app.post("/read-ingredients", response_model=ReadIngredientsResponse)
async def read_ingredients(
    file: UploadFile = File(None),
    image_url: str = Form(None),
    skin_type: SkinType = Form(...)
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
        
        # Check if ingredients not found
        if extracted_text.lower() == 'ingredients not found' or (len(extracted_text.split()) < 3 and 'not' in extracted_text.lower()):
            return {
                "extracted_ingredients": ["ingredients not found"],
                "harmful_ingredients_found": [],
                "is_safe": False,
                "total_harmful_ingredients": 0,
                "recommendations": {
                    "products": [],
                    "recommendation_count": 0
                }
            }
            
        # Parse ingredients into list
        ingredients_list = parse_ingredients_to_list(extracted_text)
        
        # Get ingredients to avoid based on skin type
        avoid_list = get_ingredients_to_avoid(skin_type)
        
        # Find harmful ingredients with detailed explanations
        harmful_ingredients = find_harmful_ingredients_with_details(extracted_text, avoid_list, skin_type)

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
                'products': [],
                'recommendation_count': 0
            }
        
        return {
            "extracted_ingredients": ingredients_list,
            "harmful_ingredients_found": harmful_ingredients,
            "is_safe": is_safe,
            "total_harmful_ingredients": len(harmful_ingredients),
            "recommendations": recommendations_result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


# === New endpoint for getting recommendations only ===
@app.post("/get-recommendations", response_model=RecommendationsResponse)
async def get_recommendations_only(request: RecommendationsRequest):
    """
    Get skincare product recommendations based on skin type from product descriptions
    
    Parameters:
        - skin_type: User's skin type
        - top_k: Number of recommendations to return
        
    Returns:
        - Products suitable for the specified skin type
    """
    try:
        skin_type = request.skin_type
        top_k = request.top_k
        
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
@app.post("/predict-skin", response_model=PredictSkinResponse)
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
        
        # Pass bytes directly for skin type prediction
        result = predict_skin_type_from_image(image_bytes, model, transform, index_label)
        
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Terjadi kesalahan dalam memproses gambar: {str(e)}"
        )
        

@app.post("/skincare-news", response_model=NewsResponse)
async def skincare_news(request: NewsRequest):
    """Get skincare news articles"""
    try:
        page = request.page
        news = get_news_list(page=page)
        return news
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/skincare-news-details", response_model=List[NewsDetailResponse])
async def skincare_news_detail(request: NewsDetailRequest):
    """Get detailed skincare news article by link"""
    try:
        article_link = request.article_link
        news = get_news(article_link)
        if not news:
            raise HTTPException(status_code=404, detail="News article details not found")
            
        # Normalize response keys to match Pydantic schema
        normalized_news = []
        for item in news:
            img = item.get("Cover_Image") or item.get("ImageUrl") or ""
            normalized_news.append({
                'Title': item.get('Title', ''),
                'Cover_Image': img,
                'Date': item.get('Date', ''),
                'Source': item.get('Source', ''),
                'Author': item.get('Author', ''),
                'Content': item.get('Content', ''),
            })
        return normalized_news
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/skincare-educations", response_model=EducationsResponse)
async def skincare_educations(request: EducationsRequest):
    """Get skincare education articles"""
    try:
        page = request.page
        link = request.link
        prev_link = request.prev_link
        
        educations = get_educations_list(page_number=page, url=link, prev_link=prev_link)
        return educations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/skincare-education-details", response_model=EducationDetailResponse)
async def skincare_education_details(request: EducationDetailRequest):
    """Get skincare education article details"""
    try:
        article_link = request.article_link
        education = get_educations_details(article_link)
        if not education:
            raise HTTPException(status_code=404, detail="Education article details not found")
        return education
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
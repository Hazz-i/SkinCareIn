from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel

import os
from google import genai
from helper.functions import get_image_from_url, get_image_from_path, extract_text_from_image, clean_extracted_text, extract_ingredients_section

load_dotenv()

app = FastAPI(title="SkincareIn", 
                description="API for skincare recommendations",
                version="1.0.0")

class ScanFoodRequest(BaseModel):
    image_url: str | None = None
    image_path: str | None = None
    
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

@app.get("/")
def index():
    return {"message": "Developernya ganteng banget?"}


@app.post("/read-ingredients", response_model=dict)
async def read_ingredients(
    data: ScanFoodRequest = Body(...)
):
    """
    Scan food image and detect food type with nutrition data
    
    Parameters:
        - image: URL to an image 
        
    Returns:
        - Detected food type
        - Nutrition data of the detected food
    """
    try:
        if not data.image_url and not data.image_path:
            raise HTTPException(status_code=400, detail="Image URL atau path diperlukan.")
        
        image_bytes = get_image_from_url(data.image_url) if data.image_url else get_image_from_path(data.image_path)
        extracted_text = extract_text_from_image(image_bytes, client)
        
        if not extracted_text:
            raise HTTPException(status_code=404, detail="Tidak ada teks yang ditemukan dalam gambar.")
        
        extracted_text = clean_extracted_text(extracted_text)
        extracted_text = extract_ingredients_section(extracted_text)
        
        return {
            "text": extracted_text,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")
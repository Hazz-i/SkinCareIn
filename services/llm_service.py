# services/llm_service.py
import os
import litellm
from core.config import settings
from core.logger import log_action

class LLMService:
    def __init__(self):
        self.model = settings.LLM_MODEL
        self.fallbacks = [m.strip() for m in settings.LLM_FALLBACKS.split(",") if m.strip()]
        litellm.drop_params = True

    async def extract_ingredients_from_image(self, base64_image: str) -> str:
        prompt = (
            "cari ingredients/bahan/komposisi dalam gambar ini dan berikan hasilnya dalam format teks biasa "
            "tanpa markdown atau formatting lainnya. buang teks yang tidak relevan seperti nama brand, nama produk, "
            "atau informasi lain yang tidak berkaitan dengan bahan, serta jika tidak terdapat ingredients sama sekali, "
            "tampilkan ingredients not found."
        )
        log_action("llm", f"Sending vision OCR prompt via LiteLLM with model: {self.model}")
        try:
            response = await litellm.acompletion(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }],
                fallbacks=self.fallbacks,
                api_key=settings.GEMINI_API_KEY
            )
            extracted_text = response.choices[0].message.content
            log_action("llm", f"LiteLLM extraction completed ({len(extracted_text)} chars)")
            return extracted_text.strip()
        except Exception as e:
            log_action("llm", f"LiteLLM invocation failed: {str(e)}", level="error")
            raise RuntimeError(f"Gagal memproses gambar dengan AI: {str(e)}")

llm_service = LLMService()

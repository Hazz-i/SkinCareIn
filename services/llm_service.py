# services/llm_service.py
import os
from typing import Dict, List

import litellm
from core.config import settings
from core.logger import log_action

class LLMService:
    def __init__(self):
        self.model = settings.LLM_MODEL
        self.fallbacks = [m.strip() for m in settings.LLM_FALLBACKS.split(",") if m.strip()]
        # Custom OpenAI-compatible gateways (9Router, LiteLLM proxy, OpenRouter, ...) expose
        # their own URL; when it is unset we talk to Google Gemini directly.
        self.api_base = settings.LLM_API_BASE.strip() or None
        self.api_key = settings.LLM_API_KEY.strip() or settings.GEMINI_API_KEY
        litellm.drop_params = True

    async def extract_ingredients_from_image(self, base64_image: str) -> str:
        prompt = (
            "find the ingredients / composition in this image and return the result as plain text "
            "without any markdown or other formatting. drop irrelevant text such as brand names, "
            "product names or any other information unrelated to the ingredients, and if there are "
            "no ingredients at all, return ingredients not found."
        )
        target = self.api_base or "provider default"
        log_action("llm", f"Sending vision OCR prompt via LiteLLM with model: {self.model} ({target})")
        try:
            request_kwargs = {
                "model": self.model,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }],
                "fallbacks": self.fallbacks,
                "api_key": self.api_key,
            }
            if self.api_base:
                request_kwargs["api_base"] = self.api_base

            response = await litellm.acompletion(**request_kwargs)
            extracted_text = response.choices[0].message.content
            log_action("llm", f"LiteLLM extraction completed ({len(extracted_text)} chars)")
            return extracted_text.strip()
        except Exception as e:
            log_action("llm", f"LiteLLM invocation failed: {str(e)}", level="error")
            raise RuntimeError(f"Failed to process the image with AI: {str(e)}")

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        max_tokens: int = 700,
        temperature: float = 0.3,
    ) -> str:
        """Text completion for the in-app assistant. The system prompt carries the scope
        restriction and the DB-grounded context, so the model cannot invent products."""
        target = self.api_base or "provider default"
        log_action("llm", f"Assistant chat via LiteLLM with model: {self.model} ({target})")
        try:
            request_kwargs = {
                "model": self.model,
                "messages": [{"role": "system", "content": system_prompt}, *messages],
                "fallbacks": self.fallbacks,
                "api_key": self.api_key,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            if self.api_base:
                request_kwargs["api_base"] = self.api_base

            response = await litellm.acompletion(**request_kwargs)
            content = response.choices[0].message.content or ""
            log_action("llm", f"Assistant chat completed ({len(content)} chars)")
            return content.strip()
        except Exception as e:
            log_action("llm", f"Assistant chat failed: {str(e)}", level="error")
            raise RuntimeError(f"Failed to reach the AI service: {str(e)}")


llm_service = LLMService()

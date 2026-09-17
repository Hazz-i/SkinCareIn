# tests/test_llm_service.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.llm_service import LLMService

@pytest.mark.asyncio
async def test_llm_service_extract_ingredients():
    llm_service = LLMService()
    fake_response = MagicMock()
    fake_choice = MagicMock()
    fake_choice.message.content = "Water, Glycerin, Niacinamide, Centella Asiatica"
    fake_response.choices = [fake_choice]

    with patch("litellm.acompletion", new=AsyncMock(return_value=fake_response)):
        result = await llm_service.extract_ingredients_from_image("fake_base64_string")
        assert "Niacinamide" in result
        assert "Centella Asiatica" in result

# schemas/chat.py
from typing import List, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    # Only the recent turns are needed; the server rebuilds context per request.
    messages: List[ChatMessage] = Field(..., min_length=1, max_length=20)


class ChatProduct(BaseModel):
    """A real catalog row that grounded the answer — safe for the client to render."""

    id: int
    name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    price: Optional[str] = None
    image_url: Optional[str] = None
    link: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    products: List[ChatProduct] = []
    # True when at least one catalog row was injected into the prompt.
    grounded: bool = False

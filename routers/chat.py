# routers/chat.py
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from core.limiter import limiter
from models.user import User
from routers.auth import get_current_user
from schemas.chat import ChatRequest, ChatResponse
from services.chat_service import ChatService

router = APIRouter(tags=["SkinSight Assistant"])


@router.post(
    "",
    response_model=ChatResponse,
    summary="Ask the SkinSight Assistant (Project-Scoped, Catalog-Grounded)",
)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def chat(
    request: Request,
    payload: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Project-scoped assistant. Off-topic questions are refused, and product answers are
    grounded in real `products` rows that are returned alongside the reply."""
    return await ChatService.reply(db, user, payload)

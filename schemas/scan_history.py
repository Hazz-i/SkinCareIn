# schemas/scan_history.py
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ScanHistoryCreate(BaseModel):
    predicted_label: str = Field(..., max_length=50)
    dry: Optional[float] = None
    normal: Optional[float] = None
    oily: Optional[float] = None
    image_url: Optional[str] = None


class ScanHistoryResponse(BaseModel):
    id: int
    predicted_label: str
    dry: Optional[float] = None
    normal: Optional[float] = None
    oily: Optional[float] = None
    image_url: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScanHistoryListResponse(BaseModel):
    items: List[ScanHistoryResponse]
    total: int
    latest: Optional[ScanHistoryResponse] = None

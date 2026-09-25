# schemas/uv_index.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class UVTimezoneSchema(BaseModel):
    id: str
    name: str

class UVReadingSchema(BaseModel):
    date: str
    time: str
    uv_index: Optional[float] = None
    level: str
    advice: str

class UVMaxSchema(BaseModel):
    time: str
    uv_index: Optional[float] = None
    level: str
    advice: str

class UVDaySchema(BaseModel):
    date: str
    max: UVMaxSchema

class UVHourlySchema(BaseModel):
    date: str
    time: str
    uv_index: Optional[float] = None
    level: str

class UVSourceSchema(BaseModel):
    attribution: str
    url: str

class UVLicenseSchema(BaseModel):
    id: str
    name: str
    url: str

class UVIndexResponse(BaseModel):
    latitude: float
    longitude: float
    timezone: UVTimezoneSchema
    now: UVReadingSchema
    today: UVDaySchema
    tomorrow: UVDaySchema
    daily: Optional[List[UVDaySchema]] = None
    hourly: Optional[List[UVHourlySchema]] = None
    source: UVSourceSchema
    license: UVLicenseSchema
    cached: bool
    fetched_at: datetime

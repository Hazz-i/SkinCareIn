# services/uv_index_service.py
import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.config import settings
from core.logger import log_action
from helper.uvindex import get_uv_forecast
from models.uv_index import UVIndexCache

class UVIndexService:
    # NOAA UV grids are coarse, so nearby coordinates share a single cache entry
    COORD_PRECISION = 2

    @staticmethod
    def _round(value: float) -> float:
        return round(float(value), UVIndexService.COORD_PRECISION)

    @staticmethod
    def _lookup(db: Session, latitude: float, longitude: float, timezone: str) -> Optional[UVIndexCache]:
        return db.query(UVIndexCache).filter(
            UVIndexCache.latitude == latitude,
            UVIndexCache.longitude == longitude,
            UVIndexCache.timezone == timezone
        ).first()

    @staticmethod
    def _store(db: Session, entry: Optional[UVIndexCache], latitude: float, longitude: float, timezone: str, payload: Dict[str, Any]) -> datetime:
        fetched_at = datetime.utcnow()
        serialized = json.dumps(payload)
        if entry:
            entry.payload = serialized
            entry.fetched_at = fetched_at
        else:
            db.add(UVIndexCache(
                latitude=latitude,
                longitude=longitude,
                timezone=timezone,
                payload=serialized,
                fetched_at=fetched_at
            ))
        db.commit()
        return fetched_at

    @staticmethod
    def _map_reading(node: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not node:
            return None
        return {
            "date": node.get("Date", ""),
            "time": node.get("Time", ""),
            "uv_index": node.get("UV_Index"),
            "level": node.get("Level", "Unknown"),
            "advice": node.get("Advice", "")
        }

    @staticmethod
    def _map_day(node: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not node:
            return None
        maximum = node.get("Max") or {}
        return {
            "date": node.get("Date", ""),
            "max": {
                "time": maximum.get("Time", ""),
                "uv_index": maximum.get("UV_Index"),
                "level": maximum.get("Level", "Unknown"),
                "advice": maximum.get("Advice", "")
            }
        }

    @staticmethod
    def _map_hour(node: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "date": node.get("Date", ""),
            "time": node.get("Time", ""),
            "uv_index": node.get("UV_Index"),
            "level": node.get("Level", "Unknown")
        }

    @staticmethod
    def _to_response(payload: Dict[str, Any], include_daily: bool, include_hourly: bool, cached: bool, fetched_at: datetime) -> Dict[str, Any]:
        timezone = payload.get("Timezone") or {}
        source = payload.get("Source") or {}
        license_info = payload.get("License") or {}
        return {
            "latitude": payload.get("Latitude"),
            "longitude": payload.get("Longitude"),
            "timezone": {
                "id": timezone.get("Id", "UTC"),
                "name": timezone.get("Name", "UTC")
            },
            "now": UVIndexService._map_reading(payload.get("Now")),
            "today": UVIndexService._map_day(payload.get("Today")),
            "tomorrow": UVIndexService._map_day(payload.get("Tomorrow")),
            "daily": [UVIndexService._map_day(day) for day in (payload.get("Daily") or [])] if include_daily else None,
            "hourly": [UVIndexService._map_hour(hour) for hour in (payload.get("Hourly") or [])] if include_hourly else None,
            "source": {
                "attribution": source.get("Attribution", "Data by uvindexapi.com"),
                "url": source.get("Url", "https://uvindexapi.com")
            },
            "license": {
                "id": license_info.get("Id", "CC-BY-SA-4.0"),
                "name": license_info.get("Name", "Creative Commons Attribution-ShareAlike 4.0 International"),
                "url": license_info.get("Url", "https://creativecommons.org/licenses/by-sa/4.0/")
            },
            "cached": cached,
            "fetched_at": fetched_at
        }

    @staticmethod
    def get_uv_index(
        db: Session,
        latitude: float,
        longitude: float,
        timezone: str = "Auto",
        include_daily: bool = True,
        include_hourly: bool = False
    ) -> Dict[str, Any]:
        lat = UVIndexService._round(latitude)
        lon = UVIndexService._round(longitude)
        tz = (timezone or "Auto").strip() or "Auto"

        entry = UVIndexService._lookup(db, lat, lon, tz)
        ttl = timedelta(hours=settings.UV_INDEX_CACHE_TTL_HOURS)
        cached = bool(entry and datetime.utcnow() - entry.fetched_at < ttl)

        if cached:
            log_action("cache", f"Cache HIT for UV Index ({lat}, {lon}, tz={tz})")
            payload = json.loads(entry.payload)
            fetched_at = entry.fetched_at
        else:
            log_action("cache", f"Cache MISS for UV Index ({lat}, {lon}, tz={tz}) -> fetching from uvindexapi.com...")
            try:
                payload = get_uv_forecast(lat, lon, timezone=tz)
            except Exception as e:
                log_action("api", f"Failed to fetch UV Index forecast for ({lat}, {lon}, tz={tz}): {e}", level="error")
                payload = None

            if payload is None:
                # Fall back to a stale cache entry rather than failing the request
                if entry:
                    log_action("cache", f"Serving stale UV Index cache for ({lat}, {lon}, tz={tz})", level="warning")
                    payload = json.loads(entry.payload)
                    fetched_at = entry.fetched_at
                    cached = True
                else:
                    raise HTTPException(status_code=502, detail="UV Index data is currently unavailable. Please try again later.")
            else:
                fetched_at = UVIndexService._store(db, entry, lat, lon, tz, payload)
                log_action("db", f"Cached UV Index forecast for ({lat}, {lon}, tz={tz})")

        return UVIndexService._to_response(payload, include_daily, include_hourly, cached, fetched_at)

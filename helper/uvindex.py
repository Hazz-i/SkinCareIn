# helper/uvindex.py
"""
UV Index API (https://uvindexapi.com) Client
Real-time UV Index reading plus daily and hourly forecasts for any coordinates.
Data is sourced from NOAA, free of charge and without API keys (CC BY-SA 4.0).
Attribution to uvindexapi.com is required wherever this data is displayed.
"""
import json
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional

from scrapling import Fetcher

from core.config import settings
from core.logger import log_action

FORECAST_PATH = "/forecast"

COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, */*"
}

# WHO Global Solar UV Index scale
UV_LEVELS = (
    (0, 2, "Low", "No protection needed. You can safely be outside."),
    (3, 5, "Moderate", "Seek shade near midday and wear sunscreen if you are outdoors."),
    (6, 7, "High", "Apply broad-spectrum sunscreen SPF 30+, a hat and sunglasses."),
    (8, 10, "Very High", "Avoid direct sun between 10:00 and 16:00 and reapply sunscreen every 2 hours."),
    (11, float("inf"), "Extreme", "Stay indoors. Unprotected skin can burn within minutes.")
)

def _fetch_api_json(url: str, timeout: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Fetch JSON from the UV Index API using Scrapling Fetcher with urllib fallback."""
    timeout = timeout or settings.UV_INDEX_API_TIMEOUT
    try:
        response = Fetcher.get(url, headers=COMMON_HEADERS, timeout=timeout)
        if response.status == 200:
            if hasattr(response, "json"):
                try:
                    return response.json()
                except Exception:
                    pass
            if hasattr(response, "body") and response.body:
                return json.loads(response.body.decode("utf-8", errors="ignore"))
    except Exception as e:
        log_action("api", f"Scrapling Fetcher JSON fallback for {url}: {e}", level="warning")

    try:
        req = urllib.request.Request(url, headers=COMMON_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="ignore"))
    except Exception as e:
        log_action("api", f"Failed to fetch JSON from {url}: {e}", level="error")
        return None

def classify_uv_index(uv_index: float) -> Dict[str, str]:
    """Map a raw UV Index value onto the WHO risk level and its skincare guidance."""
    if uv_index is None:
        return {"Level": "Unknown", "Advice": "UV Index unavailable for this hour."}

    value = max(float(uv_index), 0.0)
    for lower, upper, level, advice in UV_LEVELS:
        if lower <= value <= upper:
            return {"Level": level, "Advice": advice}
    return {"Level": "Extreme", "Advice": UV_LEVELS[-1][3]}

def _reading(node: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Normalize a 'now' style node (date, time, uv_index)."""
    if not node:
        return None
    uv_index = node.get("uv_index")
    return {
        "Date": node.get("date", ""),
        "Time": node.get("time", ""),
        "UV_Index": uv_index,
        **classify_uv_index(uv_index)
    }

def _day(node: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Normalize a 'today'/'tomorrow'/daily node (date + max reading)."""
    if not node:
        return None
    maximum = node.get("max") or {}
    uv_index = maximum.get("uv_index")
    return {
        "Date": node.get("date", ""),
        "Max": {
            "Time": maximum.get("time", ""),
            "UV_Index": uv_index,
            **classify_uv_index(uv_index)
        }
    }

def _hour(node: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a single hourly forecast entry."""
    uv_index = node.get("uv_index")
    return {
        "Date": node.get("date", ""),
        "Time": node.get("time", ""),
        "UV_Index": uv_index,
        "Level": classify_uv_index(uv_index)["Level"]
    }

def _normalize(data: Dict[str, Any]) -> Dict[str, Any]:
    """Map the uvindexapi.com response into the internal Title_Cased shape."""
    timezone = data.get("timezone") or {}
    meta = data.get("meta") or {}
    source = meta.get("source") or {}
    license_info = meta.get("license") or {}

    return {
        "Latitude": data.get("latitude"),
        "Longitude": data.get("longitude"),
        "Timezone": {
            "Id": timezone.get("id", "UTC"),
            "Name": timezone.get("name", "UTC")
        },
        "Now": _reading(data.get("now")),
        "Today": _day(data.get("today")),
        "Tomorrow": _day(data.get("tomorrow")),
        "Daily": [_day(day) for day in (data.get("daily") or [])],
        "Hourly": [_hour(hour) for hour in (data.get("hourly") or [])],
        "Source": {
            "Attribution": source.get("attribution", "Data by uvindexapi.com"),
            "Url": source.get("url", "https://uvindexapi.com")
        },
        "License": {
            "Id": license_info.get("id", "CC-BY-SA-4.0"),
            "Name": license_info.get("name", "Creative Commons Attribution-ShareAlike 4.0 International"),
            "Url": license_info.get("url", "https://creativecommons.org/licenses/by-sa/4.0/")
        }
    }

def get_uv_forecast(
    latitude: float,
    longitude: float,
    timezone: str = "Auto",
    daily: bool = True,
    hourly: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Retrieve the current UV Index, today/tomorrow maximums and optional daily & hourly forecasts.
    Returns None when the upstream API is unreachable or rejects the coordinates.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone,
        "daily": str(bool(daily)).lower(),
        "hourly": str(bool(hourly)).lower()
    }
    url = f"{settings.UV_INDEX_API_BASE_URL}{FORECAST_PATH}?{urllib.parse.urlencode(params)}"
    log_action("api", f"Fetching UV Index forecast for ({latitude}, {longitude}) tz={timezone} from uvindexapi.com...")

    data = _fetch_api_json(url)
    if not data or not data.get("ok"):
        message = data.get("message") if isinstance(data, dict) else None
        log_action("api", f"UV Index API returned no usable data for ({latitude}, {longitude}): {message}", level="warning")
        return None

    normalized = _normalize(data)
    now_level = (normalized.get("Now") or {}).get("Level")
    log_action("api", f"UV Index forecast ready for ({latitude}, {longitude}) tz={timezone} (now: {now_level})")
    return normalized

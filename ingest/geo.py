"""
Shared geospatial helpers for coordinate-based station resolution.

Used by ingest/noaa_station_index.py (local nearest-neighbor over the
mirrored NOAA station table) and ingest/usgs_ingest.py (ranking live bBox
results by real distance, since USGS returns everything in the box
unsorted).
"""
import math


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km between two lat/lon points."""
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(d_lon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

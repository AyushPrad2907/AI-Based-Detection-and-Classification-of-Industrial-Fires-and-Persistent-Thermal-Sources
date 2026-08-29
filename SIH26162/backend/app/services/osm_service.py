"""
SIH26162 — OpenStreetMap (OSM) / Overpass Data Service.

Queries OpenStreetMap via the Overpass API to determine geospatial and industrial context
for detected thermal anomalies (e.g., proximity to refineries, power plants, industrial parks,
foundries, pipelines, and storage tanks).

Includes spatial quantization caching, rate-limiting safeguards, timeout handling,
and offline fallbacks.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import httpx

from app.config import settings
from ml.utils.geo_utils import haversine_distance

logger = logging.getLogger(__name__)

# Default search radius in meters
DEFAULT_SEARCH_RADIUS_METERS = 5000

# OSM request timeout: 2s connect + 2.5s read keeps worst-case < 5s
# The Overpass QL [timeout:8] is only effective if the server is reachable.
OSM_CONNECT_TIMEOUT = 2.0
OSM_READ_TIMEOUT = 2.5

# Public Overpass API mirrors for automatic failover
OVERPASS_FALLBACK_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

# Overpass QL query template for industrial, energy, and hazardous infrastructure
OVERPASS_INDUSTRIAL_QUERY_TEMPLATE = """
[out:json][timeout:8];
(
  node["landuse"="industrial"](around:{radius},{lat},{lon});
  way["landuse"="industrial"](around:{radius},{lat},{lon});
  node["industrial"](around:{radius},{lat},{lon});
  way["industrial"](around:{radius},{lat},{lon});
  node["power"~"plant|generator|substation"](around:{radius},{lat},{lon});
  way["power"~"plant|generator|substation"](around:{radius},{lat},{lon});
  node["man_made"~"works|petroleum_refinery|flare|pipeline|storage_tank|kiln|chimney"](around:{radius},{lat},{lon});
  way["man_made"~"works|petroleum_refinery|flare|pipeline|storage_tank|kiln|chimney"](around:{radius},{lat},{lon});
  node["building"="industrial"](around:{radius},{lat},{lon});
  way["building"="industrial"](around:{radius},{lat},{lon});
);
out center;
"""


class OSMService:
    """
    Client for querying OpenStreetMap industrial infrastructure context.
    Timeout strategy: 2s connect + 2.5s read (total worst-case ≈ 4.5s).
    Falls back gracefully to alternative Overpass mirrors or offline fallback when unreachable.
    """

    def __init__(
        self,
        overpass_url: Optional[str] = None,
        timeout_seconds: float = OSM_READ_TIMEOUT,  # used for sync client
        cache_ttl_seconds: int = 3600,
    ):
        primary_url = (overpass_url or settings.osm_overpass_url or "https://overpass-api.de/api/interpreter").rstrip("/")
        self.overpass_url = primary_url
        # Multi-mirror list with primary endpoint first
        fallback_urls = [url.rstrip("/") for url in OVERPASS_FALLBACK_URLS if url.rstrip("/") != primary_url]
        self.overpass_urls = [primary_url] + fallback_urls
        self.timeout_seconds = timeout_seconds
        self.cache_ttl_seconds = cache_ttl_seconds
        # In-memory spatial cache: key -> (timestamp, result_dict)
        self._cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}

    def _get_cache_key(self, lat: float, lon: float, radius: int) -> str:
        """
        Quantize coordinates to ~100m grid for spatial cache efficiency.
        """
        grid_lat = round(lat, 3)
        grid_lon = round(lon, 3)
        return f"{grid_lat}:{grid_lon}:{radius}"

    def clear_cache(self) -> None:
        """Clear cached OSM query responses."""
        self._cache.clear()

    def _parse_overpass_elements(
        self,
        elements: List[Dict[str, Any]],
        lat: float,
        lon: float,
    ) -> List[Dict[str, Any]]:
        """
        Parse raw Overpass JSON elements into standardized facility records with distances.
        """
        facilities: List[Dict[str, Any]] = []

        for el in elements:
            tags = el.get("tags", {})
            # Determine element center coordinate
            if "center" in el:
                el_lat = float(el["center"]["lat"])
                el_lon = float(el["center"]["lon"])
            elif "lat" in el and "lon" in el:
                el_lat = float(el["lat"])
                el_lon = float(el["lon"])
            else:
                continue

            dist_m = haversine_distance(lat, lon, el_lat, el_lon, unit="meters")

            # Determine facility category/type
            name = tags.get("name", tags.get("description", "Unnamed Industrial Site"))
            facility_type = (
                tags.get("man_made")
                or tags.get("industrial")
                or tags.get("power")
                or tags.get("landuse")
                or tags.get("building")
                or "industrial_site"
            )

            facilities.append({
                "osm_id": el.get("id"),
                "osm_type": el.get("type"),
                "name": name,
                "facility_type": facility_type,
                "latitude": el_lat,
                "longitude": el_lon,
                "distance_meters": round(dist_m, 1),
                "tags": tags,
            })

        # Sort by proximity
        facilities.sort(key=lambda x: x["distance_meters"])
        return facilities

    async def get_industrial_context(
        self,
        latitude: float,
        longitude: float,
        radius_m: int = DEFAULT_SEARCH_RADIUS_METERS,
    ) -> Dict[str, Any]:
        """
        Query nearby industrial facilities and compute proximity metrics asynchronously.

        Args:
            latitude: Target latitude.
            longitude: Target longitude.
            radius_m: Search radius in meters (default 5,000m).

        Returns:
            Dictionary with industrial context and nearest facility details.
        """
        cache_key = self._get_cache_key(latitude, longitude, radius_m)
        now = time.time()

        if cache_key in self._cache:
            ts, cached_res = self._cache[cache_key]
            if (now - ts) < self.cache_ttl_seconds:
                return cached_res

        query = OVERPASS_INDUSTRIAL_QUERY_TEMPLATE.format(
            radius=radius_m,
            lat=latitude,
            lon=longitude,
        )

        last_status_code = None
        _timeout = httpx.Timeout(connect=OSM_CONNECT_TIMEOUT, read=OSM_READ_TIMEOUT, write=5.0, pool=5.0)

        for target_url in self.overpass_urls:
            try:
                async with httpx.AsyncClient(timeout=_timeout) as client:
                    resp = await client.post(target_url, data={"data": query})

                if resp.status_code != 200:
                    last_status_code = resp.status_code
                    logger.warning(f"Overpass mirror {target_url} returned HTTP {resp.status_code}. Trying next mirror...")
                    continue

                data = resp.json()
                elements = data.get("elements", [])
                facilities = self._parse_overpass_elements(elements, latitude, longitude)

                if facilities:
                    nearest = facilities[0]
                    min_dist = nearest["distance_meters"]
                    result = {
                        "is_industrial_nearby": min_dist <= 2000.0,
                        "min_distance_m": min_dist,
                        "min_distance_km": round(min_dist / 1000.0, 3),
                        "nearest_facility_name": nearest["name"],
                        "nearest_facility_type": nearest["facility_type"],
                        "total_facilities_in_radius": len(facilities),
                        "facilities": facilities[:10],
                        "query_latitude": latitude,
                        "query_longitude": longitude,
                        "search_radius_m": radius_m,
                        "status": "success",
                    }
                else:
                    result = {
                        "is_industrial_nearby": False,
                        "min_distance_m": float(radius_m),
                        "min_distance_km": round(float(radius_m) / 1000.0, 3),
                        "nearest_facility_name": None,
                        "nearest_facility_type": None,
                        "total_facilities_in_radius": 0,
                        "facilities": [],
                        "query_latitude": latitude,
                        "query_longitude": longitude,
                        "search_radius_m": radius_m,
                        "status": "no_facilities_found",
                    }

                self._cache[cache_key] = (now, result)
                return result
            except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError, httpx.HTTPError) as err:
                logger.warning(f"Overpass mirror {target_url} request failed ({type(err).__name__}). Trying next mirror...")
                continue
            except Exception as err:
                logger.warning(f"Unexpected error with Overpass mirror {target_url} ({type(err).__name__}). Trying next mirror...")
                continue

        reason = f"service_unavailable_http_{last_status_code}" if last_status_code else "offline_fallback"
        return self._fallback_context(latitude, longitude, radius_m, reason=reason)

    def get_industrial_context_sync(
        self,
        latitude: float,
        longitude: float,
        radius_m: int = DEFAULT_SEARCH_RADIUS_METERS,
    ) -> Dict[str, Any]:
        """
        Synchronous wrapper for batch pipelines and scripts.
        """
        cache_key = self._get_cache_key(latitude, longitude, radius_m)
        now = time.time()

        if cache_key in self._cache:
            ts, cached_res = self._cache[cache_key]
            if (now - ts) < self.cache_ttl_seconds:
                return cached_res

        query = OVERPASS_INDUSTRIAL_QUERY_TEMPLATE.format(
            radius=radius_m,
            lat=latitude,
            lon=longitude,
        )

        last_status_code = None
        _timeout = httpx.Timeout(connect=OSM_CONNECT_TIMEOUT, read=OSM_READ_TIMEOUT, write=5.0, pool=5.0)

        for target_url in self.overpass_urls:
            try:
                with httpx.Client(timeout=_timeout) as client:
                    resp = client.post(target_url, data={"data": query})

                if resp.status_code != 200:
                    last_status_code = resp.status_code
                    continue

                data = resp.json()
                elements = data.get("elements", [])
                facilities = self._parse_overpass_elements(elements, latitude, longitude)

                if facilities:
                    nearest = facilities[0]
                    min_dist = nearest["distance_meters"]
                    result = {
                        "is_industrial_nearby": min_dist <= 2000.0,
                        "min_distance_m": min_dist,
                        "min_distance_km": round(min_dist / 1000.0, 3),
                        "nearest_facility_name": nearest["name"],
                        "nearest_facility_type": nearest["facility_type"],
                        "total_facilities_in_radius": len(facilities),
                        "facilities": facilities[:10],
                        "query_latitude": latitude,
                        "query_longitude": longitude,
                        "search_radius_m": radius_m,
                        "status": "success",
                    }
                else:
                    result = {
                        "is_industrial_nearby": False,
                        "min_distance_m": float(radius_m),
                        "min_distance_km": round(float(radius_m) / 1000.0, 3),
                        "nearest_facility_name": None,
                        "nearest_facility_type": None,
                        "total_facilities_in_radius": 0,
                        "facilities": [],
                        "query_latitude": latitude,
                        "query_longitude": longitude,
                        "search_radius_m": radius_m,
                        "status": "no_facilities_found",
                    }

                self._cache[cache_key] = (now, result)
                return result
            except Exception:
                continue

        reason = f"service_unavailable_http_{last_status_code}" if last_status_code else "service_unavailable"
        return self._fallback_context(latitude, longitude, radius_m, reason=reason)

    async def get_land_use(self, latitude: float, longitude: float, radius_m: int = 1000) -> Dict[str, Any]:
        """
        Backward compatible alias for land-use context query.
        """
        return await self.get_industrial_context(latitude=latitude, longitude=longitude, radius_m=radius_m)

    def _fallback_context(self, lat: float, lon: float, radius_m: int, reason: str = "offline_fallback") -> Dict[str, Any]:
        """
        Safe fallback context when Overpass API is unreachable or times out.
        """
        return {
            "is_industrial_nearby": False,
            "min_distance_m": float(radius_m),
            "min_distance_km": round(float(radius_m) / 1000.0, 3),
            "nearest_facility_name": None,
            "nearest_facility_type": None,
            "total_facilities_in_radius": 0,
            "facilities": [],
            "query_latitude": lat,
            "query_longitude": lon,
            "search_radius_m": radius_m,
            "status": reason,
        }

"""
SIH26162 — Geospatial Utility Functions.

Production-grade geospatial calculations for spatial clustering,
distance metrics, bounding box validation, and industrial proximity analysis.
"""

import math
from typing import Optional, Sequence, Tuple, Union
import numpy as np


# Earth's mean radius in meters and kilometers
EARTH_RADIUS_METERS: float = 6371008.8
EARTH_RADIUS_KM: float = 6371.0088


def haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    unit: str = "meters",
) -> float:
    """
    Calculate the great-circle distance between two geographic coordinates on Earth.

    Args:
        lat1: Latitude of point 1 in decimal degrees.
        lon1: Longitude of point 1 in decimal degrees.
        lat2: Latitude of point 2 in decimal degrees.
        lon2: Longitude of point 2 in decimal degrees.
        unit: 'meters' (default), 'km', or 'miles'.

    Returns:
        Great-circle distance in the requested unit.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    radius = EARTH_RADIUS_METERS if unit == "meters" else EARTH_RADIUS_KM
    dist = radius * c

    if unit == "miles":
        return dist * 0.621371
    return dist


def haversine_distance_matrix(
    coords1: np.ndarray,
    coords2: Optional[np.ndarray] = None,
    unit: str = "meters",
) -> np.ndarray:
    """
    Compute pairwise Haversine distance matrix between two sets of (lat, lon) coordinates in degrees.

    Args:
        coords1: Array of shape (N, 2) where col 0 is lat, col 1 is lon.
        coords2: Array of shape (M, 2). If None, computes pairwise distance within coords1.
        unit: 'meters' (default) or 'km'.

    Returns:
        Distance matrix of shape (N, M) in requested unit.
    """
    if coords2 is None:
        coords2 = coords1

    coords1_rad = np.radians(coords1)
    coords2_rad = np.radians(coords2)

    lat1 = coords1_rad[:, 0, np.newaxis]
    lon1 = coords1_rad[:, 1, np.newaxis]
    lat2 = coords2_rad[:, 0]
    lon2 = coords2_rad[:, 1]

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    )
    # Clip for floating point safety
    a = np.clip(a, 0.0, 1.0)
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))

    radius = EARTH_RADIUS_METERS if unit == "meters" else EARTH_RADIUS_KM
    return radius * c


def point_in_bbox(
    lat: float,
    lon: float,
    bbox: Sequence[Union[int, float]],
) -> bool:
    """
    Check if a geographic point is within a bounding box (min_lon, min_lat, max_lon, max_lat).

    Args:
        lat: Point latitude.
        lon: Point longitude.
        bbox: (min_lon, min_lat, max_lon, max_lat) / (West, South, East, North).

    Returns:
        True if point lies within or on the bounding box boundaries.
    """
    if len(bbox) != 4:
        raise ValueError(f"Bounding box must contain 4 elements (min_lon, min_lat, max_lon, max_lat). Got: {bbox}")
    min_lon, min_lat, max_lon, max_lat = (float(x) for x in bbox)
    return (min_lat <= lat <= max_lat) and (min_lon <= lon <= max_lon)


def calculate_cluster_centroid(
    lats: Sequence[float],
    lons: Sequence[float],
) -> Tuple[float, float]:
    """
    Compute geographic centroid for a collection of coordinates using 3D cartesian projection
    to avoid distortion across longitudes and high latitudes.

    Args:
        lats: Sequence of latitudes in degrees.
        lons: Sequence of longitudes in degrees.

    Returns:
        (centroid_lat, centroid_lon) in decimal degrees.
    """
    if len(lats) == 0 or len(lons) == 0 or len(lats) != len(lons):
        raise ValueError("Latitudes and longitudes must be non-empty and equal length.")

    if len(lats) == 1:
        return float(lats[0]), float(lons[0])

    rad_lats = np.radians(lats)
    rad_lons = np.radians(lons)

    x = np.cos(rad_lats) * np.cos(rad_lons)
    y = np.cos(rad_lats) * np.sin(rad_lons)
    z = np.sin(rad_lats)

    mean_x = float(np.mean(x))
    mean_y = float(np.mean(y))
    mean_z = float(np.mean(z))

    lon = math.atan2(mean_y, mean_x)
    hyp = math.sqrt(mean_x * mean_x + mean_y * mean_y)
    lat = math.atan2(mean_z, hyp)

    return float(math.degrees(lat)), float(math.degrees(lon))


def bounding_box_around_point(
    lat: float,
    lon: float,
    radius_km: float,
) -> Tuple[float, float, float, float]:
    """
    Compute an approximate geographic bounding box (min_lon, min_lat, max_lon, max_lat)
    enclosing a circular radius around a central point.

    Args:
        lat: Center latitude.
        lon: Center longitude.
        radius_km: Search radius in kilometers.

    Returns:
        (min_lon, min_lat, max_lon, max_lat)
    """
    delta_lat = radius_km / 111.0
    cos_lat = math.cos(math.radians(lat))
    delta_lon = radius_km / (111.0 * max(0.01, cos_lat))

    min_lat = max(-90.0, lat - delta_lat)
    max_lat = min(90.0, lat + delta_lat)
    min_lon = max(-180.0, lon - delta_lon)
    max_lon = min(180.0, lon + delta_lon)

    return (float(min_lon), float(min_lat), float(max_lon), float(max_lat))

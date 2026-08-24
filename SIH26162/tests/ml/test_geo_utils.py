"""
SIH26162 — Unit Tests for Geospatial Utilities.
"""

import math
import numpy as np
import pytest

from ml.utils.geo_utils import (
    bounding_box_around_point,
    calculate_cluster_centroid,
    haversine_distance,
    haversine_distance_matrix,
    point_in_bbox,
)


def test_haversine_distance_known_points():
    # Distance between New Delhi (28.6139, 77.2090) and Mumbai (19.0760, 72.8777) ~ 1148 km
    dist_m = haversine_distance(28.6139, 77.2090, 19.0760, 72.8777, unit="meters")
    dist_km = haversine_distance(28.6139, 77.2090, 19.0760, 72.8777, unit="km")

    assert 1140000 <= dist_m <= 1160000
    assert 1140 <= dist_km <= 1160


def test_haversine_zero_distance():
    dist = haversine_distance(12.9716, 77.5946, 12.9716, 77.5946, unit="meters")
    assert abs(dist) < 1e-4


def test_haversine_distance_matrix():
    coords = np.array([
        [28.6139, 77.2090],
        [19.0760, 72.8777],
        [13.0827, 80.2707],
    ])
    mat = haversine_distance_matrix(coords, unit="km")

    assert mat.shape == (3, 3)
    assert np.allclose(np.diag(mat), 0.0)
    assert np.allclose(mat, mat.T)  # Symmetric
    assert mat[0, 1] > 1000.0


def test_point_in_bbox():
    india_bbox = (68.0, 6.0, 97.0, 37.0)
    # Delhi inside
    assert point_in_bbox(28.6139, 77.2090, india_bbox) is True
    # London outside
    assert point_in_bbox(51.5074, -0.1278, india_bbox) is False


def test_calculate_cluster_centroid():
    lats = [28.6, 28.7, 28.65]
    lons = [77.2, 77.3, 77.25]
    cent_lat, cent_lon = calculate_cluster_centroid(lats, lons)

    assert 28.6 <= cent_lat <= 28.7
    assert 77.2 <= cent_lon <= 77.3


def test_bounding_box_around_point():
    lat, lon = 20.0, 80.0
    min_lon, min_lat, max_lon, max_lat = bounding_box_around_point(lat, lon, radius_km=5.0)

    assert min_lat < lat < max_lat
    assert min_lon < lon < max_lon

"""
SIH26162 — Unit Tests for Thermal Detector (Persistence & Clustering).
"""

import pandas as pd
import pytest

from ml.models.thermal_detector import ThermalDetector


def test_thermal_detector_clustering(tmp_path):
    # Create 3 points in cluster A (co-located across dates) and 1 isolated point B
    df = pd.DataFrame([
        # Cluster A (lat=22.000, lon=85.000)
        {"latitude": 22.0001, "longitude": 85.0001, "acq_datetime": "2026-08-20 12:00:00", "frp": 15.0, "daynight": "N"},
        {"latitude": 22.0002, "longitude": 85.0003, "acq_datetime": "2026-08-21 12:00:00", "frp": 20.0, "daynight": "N"},
        {"latitude": 22.0000, "longitude": 85.0002, "acq_datetime": "2026-08-22 12:00:00", "frp": 18.0, "daynight": "N"},
        # Noise point B (lat=28.000, lon=75.000)
        {"latitude": 28.0000, "longitude": 75.0000, "acq_datetime": "2026-08-22 12:00:00", "frp": 5.0, "daynight": "D"},
    ])

    detector = ThermalDetector(spatial_eps_meters=1000.0, min_samples=2, min_persistence_observations=2)
    df_out, clusters = detector.fit_predict_clusters(df)

    assert len(clusters) == 1
    c = clusters[0]
    assert c.observation_count == 3
    assert c.is_persistent is True
    assert c.duration_days >= 1.9
    assert c.night_ratio == 1.0
    assert abs(c.centroid_lat - 22.0) < 0.01

    # Check enrichment method
    df_enriched = detector.enrich_dataframe_with_persistence(df)
    assert "persistence_count" in df_enriched.columns
    assert "persistence_days" in df_enriched.columns
    assert df_enriched["persistence_count"].max() == 3

    # Check single point prediction
    pred_res = detector.predict({"latitude": 22.0001, "longitude": 85.0001})
    assert pred_res["is_persistent"] is True

    # Save & Load roundtrip
    cluster_file = tmp_path / "clusters.json"
    detector.save(cluster_file)
    assert cluster_file.exists()

    det_loaded = ThermalDetector()
    det_loaded.load(cluster_file)
    assert len(det_loaded.clusters_) == 1
    assert det_loaded.clusters_[0].observation_count == 3

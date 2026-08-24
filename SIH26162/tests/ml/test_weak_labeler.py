"""
SIH26162 — Unit Tests for Weak Supervision Labeler.
"""

import pandas as pd
import pytest

from ml.preprocessing.weak_labeler import CLASS_LABELS, WeakSupervisionLabeler


def test_weak_labeler_classes():
    labeler = WeakSupervisionLabeler()
    assert "persistent_industrial" in CLASS_LABELS
    assert "industrial_fire" in CLASS_LABELS
    assert "wildfire" in CLASS_LABELS
    assert "agricultural_burn" in CLASS_LABELS
    assert "uncertain_anomaly" in CLASS_LABELS


def test_weak_labeler_rules():
    labeler = WeakSupervisionLabeler()

    # Case 1: Persistent industrial flare near industrial facility
    rec_flare = {
        "latitude": 20.0,
        "longitude": 80.0,
        "frp": 18.0,
        "confidence_score": 90.0,
        "dist_to_industrial_km": 0.5,
        "persistence_count": 4,
        "persistence_days": 3.0,
        "is_night": 1.0,
    }
    lbl, conf, reason = labeler.assign_label(rec_flare)
    assert lbl == "persistent_industrial"
    assert conf > 0.7

    # Case 2: Acute industrial fire (spike in industrial zone)
    rec_ind_fire = {
        "latitude": 20.0,
        "longitude": 80.0,
        "frp": 75.0,
        "confidence_score": 95.0,
        "dist_to_industrial_km": 0.3,
        "persistence_count": 1,
    }
    lbl, conf, reason = labeler.assign_label(rec_ind_fire)
    assert lbl == "industrial_fire"

    # Case 3: Wildfire (high FRP in remote forest)
    rec_wildfire = {
        "latitude": 30.0,
        "longitude": 75.0,
        "frp": 60.0,
        "brightness_primary": 355.0,
        "brightness_secondary": 300.0,
        "confidence_score": 90.0,
        "dist_to_industrial_km": 15.0,
        "persistence_count": 1,
    }
    lbl, conf, reason = labeler.assign_label(rec_wildfire)
    assert lbl == "wildfire"

    # Case 4: Low confidence anomaly
    rec_low_conf = {
        "confidence_score": 25.0,
        "frp": 0.2,
        "brightness_primary": 305.0,
    }
    lbl, conf, reason = labeler.assign_label(rec_low_conf)
    assert lbl == "uncertain_anomaly"


def test_weak_labeler_dataframe_generation():
    labeler = WeakSupervisionLabeler()
    df = pd.DataFrame([
        {"latitude": 20.0, "longitude": 80.0, "frp": 55.0, "dist_to_industrial_km": 0.2, "confidence_score": 90.0},
        {"latitude": 22.0, "longitude": 82.0, "frp": 8.0, "dist_to_industrial_km": 10.0, "confidence_score": 80.0},
    ])
    df_labeled = labeler.generate_labels(df)
    assert "weak_label" in df_labeled.columns
    assert "label_confidence" in df_labeled.columns
    assert "label_reason" in df_labeled.columns
    assert len(df_labeled) == 2

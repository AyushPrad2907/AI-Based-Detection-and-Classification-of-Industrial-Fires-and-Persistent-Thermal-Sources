"""
SIH26162 — Unit Tests for Physics-Informed Synthetic Industrial Fire Generator.
"""

from pathlib import Path
import pytest
import pandas as pd

from ml.preprocessing.synthetic_generator import SyntheticFireGenerator
from ml.preprocessing.weak_labeler import WeakSupervisionLabeler


def test_synthetic_generator_creates_valid_observations():
    generator = SyntheticFireGenerator(seed=42)
    df = generator.generate_industrial_fires(count=150)

    assert len(df) == 150
    assert "latitude" in df.columns
    assert "longitude" in df.columns
    assert "frp" in df.columns
    assert "brightness_primary" in df.columns
    assert "dist_to_industrial_km" in df.columns
    assert "is_synthetic" in df.columns

    # Check physics bounds
    assert (df["frp"] >= 50.0).all(), "All industrial fire samples should have acute FRP >= 50 MW"
    assert (df["dist_to_industrial_km"] <= 2.0).all(), "All samples should be within 2.0 km of an industrial facility"
    assert (df["brightness_primary"] >= 340.0).all(), "Primary brightness should reflect severe thermal output"


def test_synthetic_samples_labeled_as_industrial_fire():
    generator = SyntheticFireGenerator(seed=42)
    df = generator.generate_industrial_fires(count=50)

    labeler = WeakSupervisionLabeler()
    labeled_df = labeler.generate_labels(df)

    assert (labeled_df["weak_label"] == "industrial_fire").all(), (
        f"All synthetic samples should be classified as industrial_fire, got: {labeled_df['weak_label'].value_counts()}"
    )

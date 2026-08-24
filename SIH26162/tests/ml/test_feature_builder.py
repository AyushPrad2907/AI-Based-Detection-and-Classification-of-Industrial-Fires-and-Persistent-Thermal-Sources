"""
SIH26162 — Unit Tests for Feature Builder.
"""

import numpy as np
import pandas as pd
import pytest

from ml.preprocessing.feature_builder import DEFAULT_FEATURE_COLUMNS, FeatureBuilder


def test_feature_builder_initialization():
    builder = FeatureBuilder()
    assert len(builder.feature_columns) == len(DEFAULT_FEATURE_COLUMNS)
    assert "brightness_diff" in builder.feature_columns
    assert "frp" in builder.feature_columns
    assert "sin_hour" in builder.feature_columns


def test_feature_builder_dataframe_transformation():
    builder = FeatureBuilder()
    sample_df = pd.DataFrame([{
        "latitude": 22.5,
        "longitude": 88.3,
        "brightness_primary": 340.5,
        "brightness_secondary": 295.0,
        "frp": 25.4,
        "confidence_score": 85.0,
        "acq_datetime": "2026-08-24 14:30:00",
        "daynight": "D",
        "scan": 0.4,
        "track": 0.5,
        "instrument": "VIIRS",
        "satellite": "N",
    }])

    feat_df = builder.build_features_df(sample_df)

    assert isinstance(feat_df, pd.DataFrame)
    assert len(feat_df) == 1
    assert list(feat_df.columns) == builder.feature_columns

    # Verify mathematical values
    assert pytest.approx(feat_df["brightness_diff"].iloc[0], 0.01) == (340.5 - 295.0)
    assert pytest.approx(feat_df["log_frp"].iloc[0], 0.01) == np.log1p(25.4)
    assert feat_df["is_viirs"].iloc[0] == 1.0


def test_feature_builder_single_vector():
    builder = FeatureBuilder()
    rec = {
        "latitude": 19.1,
        "longitude": 72.8,
        "brightness_primary": 320.0,
        "brightness_secondary": 290.0,
        "frp": 12.0,
        "confidence_score": 75.0,
        "daynight": "N",
        "acq_datetime": "2026-08-24 22:00:00",
    }
    vec = builder.build_single_feature_vector(rec)
    assert isinstance(vec, np.ndarray)
    assert len(vec) == len(builder.feature_columns)
    assert not np.isnan(vec).any()


def test_feature_builder_empty_df():
    builder = FeatureBuilder()
    empty_df = pd.DataFrame()
    feat_df = builder.build_features_df(empty_df)
    assert feat_df.empty
    assert list(feat_df.columns) == builder.feature_columns

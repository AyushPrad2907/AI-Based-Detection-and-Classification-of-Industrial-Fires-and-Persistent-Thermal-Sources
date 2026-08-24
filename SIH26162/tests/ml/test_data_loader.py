"""
SIH26162 — Unit Tests for Dataset Loader.
"""

from pathlib import Path
import pandas as pd
import pytest

from ml.utils.data_utils import FIRMSDatasetLoader, load_csv


def test_load_csv_nonexistent():
    with pytest.raises(FileNotFoundError):
        load_csv("non_existent_file_xyz_123.csv")


def test_dataset_loader_discovery():
    loader = FIRMSDatasetLoader(data_dir="data/processed/firms")
    files = loader.discover_files()
    assert isinstance(files, list)
    if files:
        assert all(f.exists() for f in files)


def test_dataset_loader_load_real_data():
    loader = FIRMSDatasetLoader(data_dir="data/processed/firms")
    df = loader.load_dataset()

    assert isinstance(df, pd.DataFrame)
    if not df.empty:
        assert "latitude" in df.columns
        assert "longitude" in df.columns
        assert "brightness_primary" in df.columns
        assert "frp" in df.columns
        assert "confidence_score" in df.columns
        assert "acq_datetime" in df.columns

        summary = loader.get_dataset_summary(df)
        assert summary["total_observations"] == len(df)
        assert "mean_frp" in summary
        assert "mean_confidence" in summary


def test_dataset_loader_filters():
    loader = FIRMSDatasetLoader(data_dir="data/processed/firms")
    df_all = loader.load_dataset()
    if not df_all.empty:
        # Test confidence filter
        df_high = loader.load_dataset(min_confidence=80.0)
        assert len(df_high) <= len(df_all)
        if not df_high.empty:
            assert (df_high["confidence_score"] >= 80.0).all()

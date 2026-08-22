"""
SIH26162 — Unit & Integration Tests for NASA FIRMS Preprocessor.
"""

from pathlib import Path
import pandas as pd
import pytest

from ml.preprocessing.firms_preprocessor import (
    FIRMSPreprocessor,
    PreprocessingValidationError,
)


@pytest.fixture
def sample_viirs_csv():
    return """latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight
28.6139,77.2090,345.2,0.38,0.36,2024-05-18,730,N,VIIRS,nominal,2.0NRT,298.4,12.5,D
19.0760,72.8777,330.1,0.40,0.37,2024-05-18,1430,N,VIIRS,h,2.0NRT,295.0,8.2,N
13.0827,80.2707,310.5,0.45,0.40,2024-05-18,045,N,VIIRS,l,2.0NRT,290.1,3.1,D
28.6139,77.2090,345.2,0.38,0.36,2024-05-18,730,N,VIIRS,nominal,2.0NRT,298.4,12.5,D
"""


@pytest.fixture
def sample_modis_csv():
    return """latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_t31,frp,daynight
22.5726,88.3639,320.4,1.0,1.0,2024-05-18,0530,Terra,MODIS,85,6.1NRT,296.2,25.0,D
12.9716,77.5946,305.0,1.2,1.1,2024-05-18,1800,Aqua,MODIS,25,6.1NRT,290.0,5.0,N
"""


@pytest.fixture
def invalid_coords_csv():
    return """latitude,longitude,bright_ti4,acq_date,acq_time,confidence
95.0000,77.2090,345.2,2024-05-18,0730,n
-91.0000,77.2090,345.2,2024-05-18,0730,n
28.6139,195.2090,345.2,2024-05-18,0730,n
28.6139,-190.2090,345.2,2024-05-18,0730,n
bad_lat,77.2090,345.2,2024-05-18,0730,n
28.6139,77.2090,345.2,2024-05-18,0730,n
"""


class TestFIRMSPreprocessorSchema:
    """Test schema and loading validation."""

    def test_load_raw_data_string(self, sample_viirs_csv):
        preprocessor = FIRMSPreprocessor()
        df = preprocessor.load_raw_data(sample_viirs_csv)
        assert not df.empty
        assert "latitude" in df.columns
        assert "bright_ti4" in df.columns

    def test_validate_schema_valid(self, sample_viirs_csv):
        preprocessor = FIRMSPreprocessor()
        df = preprocessor.load_raw_data(sample_viirs_csv)
        is_valid, missing = preprocessor.validate_schema(df)
        assert is_valid is True
        assert missing == []

    def test_validate_schema_missing_columns(self):
        preprocessor = FIRMSPreprocessor()
        bad_df = pd.DataFrame({"latitude": [28.0], "longitude": [77.0]})
        is_valid, missing = preprocessor.validate_schema(bad_df)
        assert is_valid is False
        assert "acq_date" in missing
        assert "acq_time" in missing


class TestFIRMSPreprocessorCoordinates:
    """Test coordinate range validation."""

    def test_validate_and_clean_coordinates(self, invalid_coords_csv):
        preprocessor = FIRMSPreprocessor()
        raw_df = preprocessor.load_raw_data(invalid_coords_csv)
        cleaned = preprocessor.validate_and_clean_coordinates(raw_df)
        # Out of 6 rows, only the last row has valid coordinates
        assert len(cleaned) == 1
        assert cleaned.iloc[0]["latitude"] == 28.6139
        assert cleaned.iloc[0]["longitude"] == 77.2090


class TestFIRMSPreprocessorTimestamps:
    """Test parsing of acq_date and 4-digit acq_time."""

    def test_parse_timestamps(self, sample_viirs_csv):
        preprocessor = FIRMSPreprocessor()
        df = preprocessor.load_raw_data(sample_viirs_csv)
        df_ts = preprocessor.parse_timestamps(df)

        assert "acq_datetime" in df_ts.columns
        # row 0 has acq_date='2024-05-18' and acq_time=730 -> 07:30
        assert df_ts.iloc[0]["acq_datetime"] == pd.Timestamp("2024-05-18 07:30:00")
        # row 1 has acq_date='2024-05-18' and acq_time=1430 -> 14:30
        assert df_ts.iloc[1]["acq_datetime"] == pd.Timestamp("2024-05-18 14:30:00")
        # row 2 has acq_date='2024-05-18' and acq_time=045 -> 00:45
        assert df_ts.iloc[2]["acq_datetime"] == pd.Timestamp("2024-05-18 00:45:00")


class TestFIRMSPreprocessorNormalization:
    """Test column normalization for VIIRS vs MODIS."""

    def test_normalize_viirs_columns(self, sample_viirs_csv):
        preprocessor = FIRMSPreprocessor()
        df = preprocessor.load_raw_data(sample_viirs_csv)
        df = preprocessor.parse_timestamps(df)
        df_norm = preprocessor.normalize_columns(df)

        assert "brightness_primary" in df_norm.columns
        assert "brightness_secondary" in df_norm.columns
        assert df_norm.iloc[0]["brightness_primary"] == 345.2
        assert df_norm.iloc[0]["brightness_secondary"] == 298.4

        # Confidence mappings
        assert df_norm.iloc[0]["confidence_category"] == "nominal"
        assert df_norm.iloc[0]["confidence_score"] == 70.0
        assert df_norm.iloc[1]["confidence_category"] == "high"
        assert df_norm.iloc[1]["confidence_score"] == 100.0
        assert df_norm.iloc[2]["confidence_category"] == "low"
        assert df_norm.iloc[2]["confidence_score"] == 30.0

    def test_normalize_modis_columns(self, sample_modis_csv):
        preprocessor = FIRMSPreprocessor()
        df = preprocessor.load_raw_data(sample_modis_csv)
        df = preprocessor.parse_timestamps(df)
        df_norm = preprocessor.normalize_columns(df)

        assert df_norm.iloc[0]["brightness_primary"] == 320.4
        assert df_norm.iloc[0]["brightness_secondary"] == 296.2
        assert df_norm.iloc[0]["confidence_score"] == 85.0
        assert df_norm.iloc[0]["confidence_category"] == "high"

        assert df_norm.iloc[1]["confidence_score"] == 25.0
        assert df_norm.iloc[1]["confidence_category"] == "low"


class TestFIRMSPreprocessorDeduplicationAndFiltering:
    """Test duplicate removal and filtering logic."""

    def test_remove_duplicates(self, sample_viirs_csv):
        preprocessor = FIRMSPreprocessor()
        df = preprocessor.load_raw_data(sample_viirs_csv)
        df = preprocessor.parse_timestamps(df)
        # sample_viirs_csv has 4 rows, rows 0 and 3 are exact duplicates
        df_dedup = preprocessor.remove_duplicates(df)
        assert len(df_dedup) == 3

    def test_filter_by_confidence(self, sample_viirs_csv):
        preprocessor = FIRMSPreprocessor(min_confidence="high")
        df = preprocessor.load_raw_data(sample_viirs_csv)
        df = preprocessor.parse_timestamps(df)
        df = preprocessor.normalize_columns(df)
        filtered = preprocessor.filter_by_confidence(df)

        assert len(filtered) == 1
        assert filtered.iloc[0]["confidence_category"] == "high"

    def test_filter_by_bbox(self, sample_viirs_csv):
        # Bounding box around Delhi (approx lon: 76-78, lat: 27-29)
        preprocessor = FIRMSPreprocessor(bbox=(76.0, 27.0, 78.0, 29.0))
        df = preprocessor.load_raw_data(sample_viirs_csv)
        filtered = preprocessor.filter_by_bbox(df)

        assert len(filtered) == 2  # rows 0 and 3 are in Delhi (28.61, 77.20)


class TestFIRMSPreprocessorEndToEnd:
    """Test end-to-end preprocess pipeline execution."""

    def test_full_pipeline_viirs(self, sample_viirs_csv, tmp_path):
        out_file = tmp_path / "processed_viirs.csv"
        preprocessor = FIRMSPreprocessor(min_confidence="nominal")

        df_out = preprocessor.preprocess(source=sample_viirs_csv, output_path=out_file)

        assert out_file.exists()
        assert len(df_out) == 2  # 1 nominal + 1 high (duplicate dropped, low dropped)
        assert "acq_datetime" in df_out.columns
        assert "brightness_primary" in df_out.columns
        assert "confidence_score" in df_out.columns

    def test_full_pipeline_missing_required_fails(self):
        preprocessor = FIRMSPreprocessor()
        bad_csv = "latitude,longitude\n28.61,77.20\n"
        with pytest.raises(PreprocessingValidationError, match="Missing required columns"):
            preprocessor.preprocess(bad_csv)

"""
SIH26162 — NASA FIRMS Data Preprocessor (Placeholder).

Will handle cleaning, filtering, and transforming raw FIRMS data
(CSV/JSON) into structured formats suitable for ML training.

NOT YET IMPLEMENTED — will be built in Phase 1.
"""

from typing import Optional
import pandas as pd


class FIRMSPreprocessor:
    """
    Preprocessor for NASA FIRMS active fire data.

    Planned transformations:
    - Parse FIRMS CSV data (latitude, longitude, brightness, confidence, etc.)
    - Filter by confidence level and region
    - Handle missing values and outliers
    - Convert timestamps to consistent timezone
    - Add derived spatial features
    """

    def __init__(self, confidence_threshold: str = "nominal"):
        self.confidence_threshold = confidence_threshold

    def load_raw_data(self, filepath: str) -> pd.DataFrame:
        """Load raw FIRMS CSV data. NOT YET IMPLEMENTED."""
        raise NotImplementedError("Will be implemented in Phase 1")

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and filter FIRMS data. NOT YET IMPLEMENTED."""
        raise NotImplementedError("Will be implemented in Phase 1")

    def preprocess(self, filepath: str) -> pd.DataFrame:
        """Full preprocessing pipeline. NOT YET IMPLEMENTED."""
        raise NotImplementedError("Will be implemented in Phase 1")

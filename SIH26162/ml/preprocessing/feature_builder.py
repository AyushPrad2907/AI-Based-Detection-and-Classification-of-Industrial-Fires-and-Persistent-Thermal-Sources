"""
SIH26162 — Feature Engineering Pipeline (Placeholder).

Will combine data from multiple sources (FIRMS, OSM, satellite)
into a unified feature vector for ML model training.

NOT YET IMPLEMENTED — will be built in Phase 2.
"""


class FeatureBuilder:
    """
    Builds feature vectors from multi-source geospatial data.

    Planned feature categories:
    - Spatial features: lat/lon, distance to nearest road/city/industrial zone
    - Temporal features: time of day, day of week, season, persistence duration
    - Spectral features: brightness temperature, FRP, NDVI, NBR
    - Contextual features: OSM land-use type, elevation, slope
    """

    def build_spatial_features(self, latitude: float, longitude: float) -> dict:
        """Extract spatial features for a coordinate. NOT YET IMPLEMENTED."""
        raise NotImplementedError("Will be implemented in Phase 2")

    def build_temporal_features(self, timestamp: str) -> dict:
        """Extract temporal features from a timestamp. NOT YET IMPLEMENTED."""
        raise NotImplementedError("Will be implemented in Phase 2")

    def build_feature_vector(self, firms_record: dict, osm_context: dict) -> list:
        """Build a complete feature vector. NOT YET IMPLEMENTED."""
        raise NotImplementedError("Will be implemented in Phase 2")

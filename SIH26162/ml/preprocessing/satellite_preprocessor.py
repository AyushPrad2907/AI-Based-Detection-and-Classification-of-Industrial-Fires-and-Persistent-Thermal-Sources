"""
SIH26162 — Satellite Imagery Preprocessor (Placeholder).

Will handle loading, tiling, and preprocessing satellite imagery
(Sentinel-2, Landsat-8/9) for feature extraction.

NOT YET IMPLEMENTED — will be built in Phase 2.
"""


class SatellitePreprocessor:
    """
    Preprocessor for satellite imagery.

    Planned capabilities:
    - Load GeoTIFF raster data using rasterio
    - Extract spectral bands relevant to fire detection (SWIR, NIR, thermal)
    - Tile large images into model-compatible patches
    - Apply radiometric calibration and atmospheric correction
    - Generate normalized indices (NDVI, NBR, etc.)
    """

    def load_raster(self, filepath: str):
        """Load a satellite raster file. NOT YET IMPLEMENTED."""
        raise NotImplementedError("Will be implemented in Phase 2")

    def extract_bands(self, raster_data, band_names: list):
        """Extract specific spectral bands. NOT YET IMPLEMENTED."""
        raise NotImplementedError("Will be implemented in Phase 2")

    def compute_indices(self, raster_data) -> dict:
        """Compute spectral indices (NDVI, NBR). NOT YET IMPLEMENTED."""
        raise NotImplementedError("Will be implemented in Phase 2")

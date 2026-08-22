"""
SIH26162 — Fire Classification Service (Placeholder).

Will orchestrate the ML model inference to classify thermal anomalies
into categories: industrial fire, wildfire, agricultural burn,
power plant, persistent industrial source, etc.

NOT YET IMPLEMENTED — will be built in Phase 3.
"""


class ClassificationService:
    """
    Service for classifying thermal anomalies.

    Will provide methods to:
    - Load the trained ML model
    - Run inference on new thermal detections
    - Combine FIRMS data + OSM context for classification
    - Return classified results with confidence scores
    """

    async def classify_thermal_source(self, latitude: float, longitude: float, brightness: float):
        """
        Classify a thermal anomaly using the ML model.

        Args:
            latitude: Latitude of the thermal detection.
            longitude: Longitude of the thermal detection.
            brightness: Brightness temperature from FIRMS data.

        Returns:
            Classification result with confidence score.

        NOT YET IMPLEMENTED.
        """
        # TODO: Implement ML model inference
        raise NotImplementedError("Classification will be implemented in Phase 3")

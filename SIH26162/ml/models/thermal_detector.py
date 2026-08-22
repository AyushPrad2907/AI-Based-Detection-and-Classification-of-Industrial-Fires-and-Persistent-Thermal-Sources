"""
SIH26162 — Persistent Thermal Source Detector (Placeholder).

Will implement a model for detecting persistent (non-fire) thermal
sources like industrial furnaces, smelters, and power plants.

NOT YET IMPLEMENTED — will be built in Phase 2.
"""

from ml.models.base_model import BaseModel


class ThermalDetector(BaseModel):
    """
    Model for detecting persistent thermal sources.

    Differs from FireClassifier in that it focuses on:
    - Long-duration thermal signatures (days to months)
    - Spatial consistency of heat sources
    - Temporal patterns (operational schedules)
    """

    def train(self, train_data, val_data=None):
        raise NotImplementedError("Will be implemented in Phase 2")

    def predict(self, input_data):
        raise NotImplementedError("Will be implemented in Phase 2")

    def evaluate(self, test_data):
        raise NotImplementedError("Will be implemented in Phase 2")

    def save(self, path):
        raise NotImplementedError("Will be implemented in Phase 2")

    def load(self, path):
        raise NotImplementedError("Will be implemented in Phase 2")

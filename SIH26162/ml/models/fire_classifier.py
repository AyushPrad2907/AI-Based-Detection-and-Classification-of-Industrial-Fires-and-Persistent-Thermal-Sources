"""
SIH26162 — Fire Classification Model (Placeholder).

Will implement a neural network for classifying thermal anomalies
into fire/thermal source categories.

NOT YET IMPLEMENTED — will be built in Phase 2.
"""

from ml.models.base_model import BaseModel


class FireClassifier(BaseModel):
    """
    Neural network model for fire type classification.

    Planned architecture:
    - Input: Feature vector from FeatureBuilder
    - Architecture: MLP or CNN (to be determined based on data)
    - Output: Multi-class classification (5 categories)
    - Categories: industrial_fire, wildfire, agricultural_burn,
                  power_plant, persistent_industrial
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

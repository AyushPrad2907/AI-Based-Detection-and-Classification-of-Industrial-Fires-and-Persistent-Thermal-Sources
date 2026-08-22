"""
SIH26162 — Abstract Base Model.

Defines the interface that all ML models must implement,
ensuring consistency across different model types.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseModel(ABC):
    """
    Abstract base class for all ML models in the pipeline.

    All models (fire classifier, thermal detector, etc.) must
    implement these methods to ensure a consistent interface.
    """

    @abstractmethod
    def train(self, train_data: Any, val_data: Any = None) -> dict:
        """
        Train the model on the provided data.

        Args:
            train_data: Training dataset.
            val_data: Validation dataset (optional).

        Returns:
            Dictionary of training metrics.
        """
        ...

    @abstractmethod
    def predict(self, input_data: Any) -> Any:
        """
        Run inference on new data.

        Args:
            input_data: Input features for prediction.

        Returns:
            Model predictions.
        """
        ...

    @abstractmethod
    def evaluate(self, test_data: Any) -> dict:
        """
        Evaluate model performance on test data.

        Args:
            test_data: Test dataset.

        Returns:
            Dictionary of evaluation metrics.
        """
        ...

    @abstractmethod
    def save(self, path: Path) -> None:
        """
        Save model weights and configuration to disk.

        Args:
            path: Directory to save the model.
        """
        ...

    @abstractmethod
    def load(self, path: Path) -> None:
        """
        Load model weights and configuration from disk.

        Args:
            path: Directory containing the saved model.
        """
        ...

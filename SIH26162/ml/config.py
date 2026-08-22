"""
SIH26162 — ML Pipeline Configuration.

Centralized configuration for model hyperparameters, data paths,
and training settings.
"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DataConfig:
    """Configuration for data paths and preprocessing."""

    raw_data_dir: Path = Path("data/raw")
    processed_data_dir: Path = Path("data/processed")
    sample_data_dir: Path = Path("data/sample")

    # NASA FIRMS data settings
    firms_source: str = "VIIRS_SNPP_NRT"  # or MODIS_NRT
    firms_date_range_days: int = 10


@dataclass
class ModelConfig:
    """Configuration for model architecture and training."""

    # Model selection
    model_type: str = "fire_classifier"  # fire_classifier | thermal_detector

    # Training hyperparameters
    learning_rate: float = 1e-3
    batch_size: int = 32
    num_epochs: int = 50
    early_stopping_patience: int = 5

    # Model architecture
    input_features: int = 12  # Number of input features (to be determined)
    hidden_layers: list = field(default_factory=lambda: [128, 64, 32])
    num_classes: int = 5  # Number of fire/thermal source categories

    # Classification categories (planned)
    class_labels: list = field(default_factory=lambda: [
        "industrial_fire",
        "wildfire",
        "agricultural_burn",
        "power_plant",
        "persistent_industrial",
    ])


@dataclass
class TrainingConfig:
    """Configuration for the training pipeline."""

    model_save_dir: Path = Path("ml/saved_models")
    log_dir: Path = Path("ml/logs")
    random_seed: int = 42
    train_split: float = 0.7
    val_split: float = 0.15
    test_split: float = 0.15

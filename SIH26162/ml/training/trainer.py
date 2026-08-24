"""
SIH26162 — Model Training Orchestrator.

Orchestrates the end-to-end training pipeline for fire and persistent thermal anomaly
classification:
1. Multi-source dataset loading & deduplication (NASA FIRMS)
2. Spatio-temporal persistence clustering
3. Weak-supervision label generation with scientific transparency
4. Feature engineering & matrix construction
5. Stratified Train / Validation / Test splitting (no data leakage)
6. Model training (Random Forest / Gradient Boosting)
7. Held-out test evaluation with confusion matrix & ROC-AUC
8. Model serialization and artifact logging
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from ml.config import TrainingConfig
from ml.evaluation.evaluator import Evaluator
from ml.models.fire_classifier import FireClassifier
from ml.models.thermal_detector import ThermalDetector
from ml.preprocessing.feature_builder import FeatureBuilder
from ml.preprocessing.weak_labeler import WeakSupervisionLabeler
from ml.utils.data_utils import FIRMSDatasetLoader

logger = logging.getLogger(__name__)


class Trainer:
    """
    Coordinates data preparation, model training, validation, and serialization.
    """

    def __init__(
        self,
        data_loader: Optional[FIRMSDatasetLoader] = None,
        model_type: str = "random_forest",
        n_estimators: int = 150,
        max_depth: Optional[int] = 12,
        model_save_dir: Union[str, Path] = "ml/saved_models",
        random_seed: int = 42,
        train_split: float = 0.70,
        val_split: float = 0.15,
        test_split: float = 0.15,
    ):
        self.data_loader = data_loader or FIRMSDatasetLoader()
        self.model_type = model_type
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.model_save_dir = Path(model_save_dir)
        self.random_seed = random_seed
        self.train_split = train_split
        self.val_split = val_split
        self.test_split = test_split

        self.feature_builder = FeatureBuilder()
        self.thermal_detector = ThermalDetector()
        self.labeler = WeakSupervisionLabeler()
        self.evaluator = Evaluator(output_dir=self.model_save_dir / "reports")
        self.classifier: Optional[FireClassifier] = None

    def prepare_dataset(
        self,
        sources: Optional[Union[str, Path, list]] = None,
    ) -> pd.DataFrame:
        """
        Load, cluster, and label the dataset for training.
        """
        logger.info("Step 1: Loading NASA FIRMS dataset...")
        df = self.data_loader.load_dataset(sources=sources)
        if df.empty:
            raise ValueError("No data loaded. Ensure processed FIRMS CSV files exist.")

        logger.info(f"Loaded {len(df)} observations.")

        logger.info("Step 2: Spatio-temporal persistence enrichment...")
        df_enriched = self.thermal_detector.enrich_dataframe_with_persistence(df)

        logger.info("Step 3: Weak supervision label generation...")
        df_labeled = self.labeler.generate_labels(df_enriched)

        return df_labeled

    def split_data(
        self,
        df: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Stratified split into Train, Validation, and Test partitions.
        Guarantees zero data leakage between partitions.
        """
        y = df["weak_label"]
        # Train + (Val+Test) split
        val_test_ratio = self.val_split + self.test_split
        train_df, val_test_df = train_test_split(
            df,
            test_size=val_test_ratio,
            random_state=self.random_seed,
            stratify=y,
        )

        # Val / Test split
        test_ratio_relative = self.test_split / val_test_ratio
        val_df, test_df = train_test_split(
            val_test_df,
            test_size=test_ratio_relative,
            random_state=self.random_seed,
            stratify=val_test_df["weak_label"],
        )

        logger.info(
            f"Dataset split: Train={len(train_df)} ({len(train_df)/len(df):.1%}), "
            f"Val={len(val_df)} ({len(val_df)/len(df):.1%}), "
            f"Test={len(test_df)} ({len(test_df)/len(df):.1%})"
        )
        return train_df.reset_index(drop=True), val_df.reset_index(drop=True), test_df.reset_index(drop=True)

    def train(
        self,
        sources: Optional[Union[str, Path, list]] = None,
        save_artifacts: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute full training and evaluation workflow.

        Returns:
            Dictionary with training history, test evaluation metrics, and feature importances.
        """
        df_prepared = self.prepare_dataset(sources=sources)
        train_df, val_df, test_df = self.split_data(df_prepared)

        # Initialize classifier
        self.classifier = FireClassifier(
            model_type=self.model_type,
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            random_state=self.random_seed,
            feature_columns=self.feature_builder.feature_columns,
        )

        # Train model
        logger.info("Step 4: Training FireClassifier...")
        train_metrics = self.classifier.train(train_data=train_df, val_data=val_df)

        # Evaluate on test set
        logger.info("Step 5: Evaluating on held-out test set...")
        test_metrics = self.evaluator.evaluate_model(
            model=self.classifier,
            test_data=test_df,
            save_report=save_artifacts,
            report_filename="test_evaluation_report.json",
        )

        feature_importances = self.classifier.get_feature_importances()

        # Save artifacts
        if save_artifacts:
            self.model_save_dir.mkdir(parents=True, exist_ok=True)
            model_path = self.model_save_dir / "fire_classifier.joblib"
            clusters_path = self.model_save_dir / "persistent_clusters.json"

            self.classifier.save(model_path)
            self.thermal_detector.save(clusters_path)

            training_summary = {
                "dataset_size": len(df_prepared),
                "train_samples": len(train_df),
                "val_samples": len(val_df),
                "test_samples": len(test_df),
                "train_metrics": train_metrics,
                "test_metrics": test_metrics,
                "feature_importances": feature_importances,
                "features_used": self.classifier.feature_columns,
                "model_type": self.model_type,
            }

            with open(self.model_save_dir / "training_summary.json", "w", encoding="utf-8") as f:
                json.dump(training_summary, f, indent=2)

            logger.info(f"Artifacts and summary written to: {self.model_save_dir}")

        return {
            "dataset_size": len(df_prepared),
            "train_metrics": train_metrics,
            "test_metrics": test_metrics,
            "feature_importances": feature_importances,
        }

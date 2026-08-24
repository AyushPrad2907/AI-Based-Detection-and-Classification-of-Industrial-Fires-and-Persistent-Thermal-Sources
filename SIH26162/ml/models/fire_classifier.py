"""
SIH26162 — Fire and Thermal Anomaly Classification Model.

Production-grade ensemble classifier (Random Forest / Gradient Boosting)
for categorizing thermal detections into industrial, wildfire, agricultural,
and persistent thermal source classes.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml.models.base_model import BaseModel
from ml.preprocessing.feature_builder import DEFAULT_FEATURE_COLUMNS, FeatureBuilder

logger = logging.getLogger(__name__)

DEFAULT_CLASS_LABELS: List[str] = [
    "persistent_industrial",
    "industrial_fire",
    "wildfire",
    "agricultural_burn",
    "uncertain_anomaly",
]


class FireClassifier(BaseModel):
    """
    Supervised classifier for multi-class thermal source identification.
    """

    def __init__(
        self,
        model_type: str = "random_forest",
        n_estimators: int = 150,
        max_depth: Optional[int] = 12,
        random_state: int = 42,
        feature_columns: Optional[List[str]] = None,
        class_labels: Optional[List[str]] = None,
    ):
        self.model_type = model_type
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state
        self.feature_columns = feature_columns or list(DEFAULT_FEATURE_COLUMNS)
        self.class_labels = class_labels or list(DEFAULT_CLASS_LABELS)
        self.pipeline: Optional[Pipeline] = None
        self.is_fitted: bool = False
        self.feature_builder = FeatureBuilder(feature_columns=self.feature_columns)
        self._init_pipeline()

    def _init_pipeline(self) -> None:
        """Initialize the preprocessing and estimator pipeline."""
        if self.model_type == "random_forest":
            estimator = RandomForestClassifier(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                random_state=self.random_state,
                class_weight="balanced",
                n_jobs=-1,
            )
        elif self.model_type == "hist_gradient_boosting":
            estimator = HistGradientBoostingClassifier(
                max_iter=self.n_estimators,
                max_depth=self.max_depth,
                random_state=self.random_state,
                class_weight="balanced",
            )
        else:
            raise ValueError(f"Unsupported model_type: '{self.model_type}'")

        self.pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("classifier", estimator),
        ])

    def _prepare_X_y(
        self,
        data: Union[pd.DataFrame, Tuple[np.ndarray, np.ndarray]],
        target_col: str = "weak_label",
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Convert input DataFrame or tuple into numpy arrays."""
        if isinstance(data, pd.DataFrame):
            if target_col not in data.columns:
                raise ValueError(f"Target column '{target_col}' not found in DataFrame.")
            feat_df = self.feature_builder.build_features_df(data)
            X = feat_df.values
            y = data[target_col].values
            return X, y
        elif isinstance(data, (tuple, list)) and len(data) == 2:
            X, y = data
            return np.asarray(X), np.asarray(y)
        else:
            raise ValueError(f"Invalid input data format: {type(data)}")

    def train(self, train_data: Any, val_data: Any = None) -> Dict[str, Any]:
        """
        Train the classifier on provided training data.

        Args:
            train_data: Training DataFrame or (X_train, y_train) tuple.
            val_data: Optional validation DataFrame or (X_val, y_val) tuple.

        Returns:
            Dictionary of training summary metrics.
        """
        X_train, y_train = self._prepare_X_y(train_data)
        if len(X_train) == 0:
            raise ValueError("Cannot train on empty dataset.")

        logger.info(f"Training {self.model_type} on {len(X_train)} samples with {X_train.shape[1]} features...")
        self.pipeline.fit(X_train, y_train)
        self.is_fitted = True

        # Train metrics
        train_preds = self.pipeline.predict(X_train)
        train_acc = float(np.mean(train_preds == y_train))

        metrics = {
            "train_samples": len(X_train),
            "train_accuracy": round(train_acc, 4),
            "classes": [str(c) for c in self.pipeline.classes_],
            "feature_count": len(self.feature_columns),
        }

        if val_data is not None:
            X_val, y_val = self._prepare_X_y(val_data)
            val_preds = self.pipeline.predict(X_val)
            val_acc = float(np.mean(val_preds == y_val))
            metrics["val_samples"] = len(X_val)
            metrics["val_accuracy"] = round(val_acc, 4)

        logger.info(f"Model training complete. Train Acc: {train_acc:.4f}")
        return metrics

    def predict(self, input_data: Any) -> np.ndarray:
        """
        Predict class labels for input observations.
        """
        if not self.is_fitted:
            raise RuntimeError("Model has not been fitted or loaded.")

        if isinstance(input_data, pd.DataFrame):
            X = self.feature_builder.build_features_df(input_data).values
        elif isinstance(input_data, dict):
            X = self.feature_builder.build_single_feature_vector(input_data).reshape(1, -1)
        elif isinstance(input_data, np.ndarray):
            X = input_data if input_data.ndim == 2 else input_data.reshape(1, -1)
        else:
            raise ValueError(f"Unsupported input type for prediction: {type(input_data)}")

        return self.pipeline.predict(X)

    def predict_proba(self, input_data: Any) -> np.ndarray:
        """
        Predict class probability distributions.
        """
        if not self.is_fitted:
            raise RuntimeError("Model has not been fitted or loaded.")

        if isinstance(input_data, pd.DataFrame):
            X = self.feature_builder.build_features_df(input_data).values
        elif isinstance(input_data, dict):
            X = self.feature_builder.build_single_feature_vector(input_data).reshape(1, -1)
        elif isinstance(input_data, np.ndarray):
            X = input_data if input_data.ndim == 2 else input_data.reshape(1, -1)
        else:
            raise ValueError(f"Unsupported input type: {type(input_data)}")

        return self.pipeline.predict_proba(X)

    def predict_single(
        self,
        record: Dict[str, Any],
        osm_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Predict class label, confidence, and class probabilities for a single observation dictionary.
        """
        if not self.is_fitted:
            raise RuntimeError("Model is not loaded or fitted.")

        vec = self.feature_builder.build_single_feature_vector(record, osm_context=osm_context).reshape(1, -1)
        probs = self.pipeline.predict_proba(vec)[0]
        classes = self.pipeline.classes_

        pred_idx = int(np.argmax(probs))
        pred_label = str(classes[pred_idx])
        pred_conf = float(probs[pred_idx])

        prob_dict = {str(cls): round(float(prob), 4) for cls, prob in zip(classes, probs)}

        return {
            "predicted_class": pred_label,
            "confidence": round(pred_conf, 4),
            "class_probabilities": prob_dict,
        }

    def get_feature_importances(self) -> Dict[str, float]:
        """
        Retrieve feature importances if supported by the underlying estimator.
        """
        if not self.is_fitted:
            return {}

        clf = self.pipeline.named_steps["classifier"]
        if hasattr(clf, "feature_importances_"):
            imps = clf.feature_importances_
            feat_imp = {feat: round(float(imp), 4) for feat, imp in zip(self.feature_columns, imps)}
            return dict(sorted(feat_imp.items(), key=lambda item: item[1], reverse=True))
        return {}

    def evaluate(self, test_data: Any) -> Dict[str, Any]:
        """
        Evaluate model on test data using classification metrics.
        """
        from ml.evaluation.metrics import Metrics

        X_test, y_test = self._prepare_X_y(test_data)
        y_pred = self.predict(X_test)
        y_prob = self.predict_proba(X_test)
        classes = [str(c) for c in self.pipeline.classes_]

        return Metrics.compute_classification_metrics(
            y_true=y_test,
            y_pred=y_pred,
            y_prob=y_prob,
            classes=classes,
        )

    def save(self, path: Union[str, Path]) -> None:
        """
        Serialize model weights, pipeline, and metadata to disk.
        """
        if not self.is_fitted:
            raise RuntimeError("Cannot save unfitted model.")

        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)

        artifact = {
            "model_type": self.model_type,
            "pipeline": self.pipeline,
            "feature_columns": self.feature_columns,
            "class_labels": self.class_labels,
            "is_fitted": self.is_fitted,
        }
        joblib.dump(artifact, p)
        logger.info(f"FireClassifier model successfully saved to: {p}")

    def load(self, path: Union[str, Path]) -> None:
        """
        Load model artifact from disk.
        """
        p = Path(path)
        if not p.exists() or not p.is_file():
            raise FileNotFoundError(f"Model artifact not found at: {p}")

        artifact = joblib.load(p)
        self.model_type = artifact.get("model_type", self.model_type)
        self.pipeline = artifact["pipeline"]
        self.feature_columns = artifact.get("feature_columns", self.feature_columns)
        self.class_labels = artifact.get("class_labels", self.class_labels)
        self.is_fitted = artifact.get("is_fitted", True)
        self.feature_builder = FeatureBuilder(feature_columns=self.feature_columns)
        logger.info(f"FireClassifier successfully loaded from: {p}")

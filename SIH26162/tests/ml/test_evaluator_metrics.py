"""
SIH26162 — Unit Tests for Evaluation Metrics and Evaluator.
"""

import numpy as np
import pytest

from ml.evaluation.evaluator import Evaluator
from ml.evaluation.metrics import Metrics


def test_compute_classification_metrics():
    y_true = ["wildfire", "wildfire", "industrial_fire", "agricultural_burn", "persistent_industrial"]
    y_pred = ["wildfire", "wildfire", "industrial_fire", "agricultural_burn", "persistent_industrial"]

    res = Metrics.compute_classification_metrics(y_true, y_pred)

    assert res["accuracy"] == 1.0
    assert res["precision_macro"] == 1.0
    assert res["recall_macro"] == 1.0
    assert res["f1_macro"] == 1.0
    assert res["sample_count"] == 5
    assert "confusion_matrix" in res
    assert "per_class" in res


def test_compute_metrics_with_probabilities():
    y_true = ["wildfire", "agricultural_burn"]
    y_pred = ["wildfire", "agricultural_burn"]
    y_prob = np.array([
        [0.9, 0.1],
        [0.2, 0.8],
    ])
    classes = ["wildfire", "agricultural_burn"]

    res = Metrics.compute_classification_metrics(y_true, y_pred, y_prob=y_prob, classes=classes)
    assert res["accuracy"] == 1.0
    assert "roc_auc_macro" in res
    assert res["roc_auc_macro"] == 1.0


def test_evaluator_markdown_report():
    evaluator = Evaluator()
    dummy_metrics = {
        "sample_count": 100,
        "accuracy": 0.95,
        "precision_macro": 0.94,
        "recall_macro": 0.93,
        "f1_macro": 0.935,
        "f1_weighted": 0.948,
        "roc_auc_macro": 0.98,
        "per_class": {
            "wildfire": {"precision": 0.95, "recall": 0.90, "f1_score": 0.92, "support": 40},
        },
        "classes": ["wildfire"],
        "confusion_matrix": {"matrix": [[40]]},
    }

    report = evaluator.generate_markdown_report(dummy_metrics)
    assert "### Model Evaluation Summary" in report
    assert "Overall Accuracy" in report
    assert "Per-Class Performance Breakdown" in report

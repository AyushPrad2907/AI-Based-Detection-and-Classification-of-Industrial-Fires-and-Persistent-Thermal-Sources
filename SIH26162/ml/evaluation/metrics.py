"""
SIH26162 — Real Evaluation Metrics.

Scientific Integrity Notice:
All evaluation metrics are computed strictly from real data predictions.
Never fabricate or hardcode accuracy, precision, recall, or AUC figures.
"""

import logging
from typing import Any, Dict, List, Optional, Sequence, Union

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)

logger = logging.getLogger(__name__)


class Metrics:
    """
    Standardized classification and clustering evaluation metrics calculation engine.
    """

    @staticmethod
    def compute_classification_metrics(
        y_true: Sequence[Any],
        y_pred: Sequence[Any],
        y_prob: Optional[np.ndarray] = None,
        classes: Optional[Sequence[str]] = None,
    ) -> Dict[str, Any]:
        """
        Compute comprehensive classification metrics.

        Args:
            y_true: True class labels.
            y_pred: Predicted class labels.
            y_prob: Optional predicted class probability matrix of shape (N, n_classes).
            classes: Ordered sequence of class label names.

        Returns:
            Dictionary containing accuracy, precision, recall, f1, confusion matrix,
            per-class breakdown, and ROC-AUC.
        """
        y_t = np.asarray(y_true)
        y_p = np.asarray(y_pred)

        if len(y_t) == 0:
            return {"status": "empty_evaluation_set"}

        # Identify unique classes present
        unique_classes = classes if classes is not None else sorted(list(set(y_t) | set(y_p)))

        acc = float(accuracy_score(y_t, y_p))
        prec_macro = float(precision_score(y_t, y_p, average="macro", zero_division=0))
        prec_weighted = float(precision_score(y_t, y_p, average="weighted", zero_division=0))
        rec_macro = float(recall_score(y_t, y_p, average="macro", zero_division=0))
        rec_weighted = float(recall_score(y_t, y_p, average="weighted", zero_division=0))
        f1_macro = float(f1_score(y_t, y_p, average="macro", zero_division=0))
        f1_weighted = float(f1_score(y_t, y_p, average="weighted", zero_division=0))

        # Confusion Matrix
        cm = confusion_matrix(y_t, y_p, labels=unique_classes)
        cm_norm = confusion_matrix(y_t, y_p, labels=unique_classes, normalize="true")
        cm_norm = np.nan_to_num(cm_norm, nan=0.0)

        # Per-class metrics
        per_class_prec = precision_score(y_t, y_p, labels=unique_classes, average=None, zero_division=0)
        per_class_rec = recall_score(y_t, y_p, labels=unique_classes, average=None, zero_division=0)
        per_class_f1 = f1_score(y_t, y_p, labels=unique_classes, average=None, zero_division=0)

        per_class_dict: Dict[str, Dict[str, float]] = {}
        for idx, cls_name in enumerate(unique_classes):
            cls_mask = y_t == cls_name
            support = int(np.sum(cls_mask))
            per_class_dict[str(cls_name)] = {
                "precision": round(float(per_class_prec[idx]), 4),
                "recall": round(float(per_class_rec[idx]), 4),
                "f1_score": round(float(per_class_f1[idx]), 4),
                "support": support,
            }

        results: Dict[str, Any] = {
            "sample_count": len(y_t),
            "classes": [str(c) for c in unique_classes],
            "accuracy": round(acc, 4),
            "precision_macro": round(prec_macro, 4),
            "precision_weighted": round(prec_weighted, 4),
            "recall_macro": round(rec_macro, 4),
            "recall_weighted": round(rec_weighted, 4),
            "f1_macro": round(f1_macro, 4),
            "f1_weighted": round(f1_weighted, 4),
            "per_class": per_class_dict,
            "confusion_matrix": {
                "labels": [str(c) for c in unique_classes],
                "matrix": cm.tolist(),
                "normalized_matrix": [[round(float(val), 4) for val in row] for row in cm_norm.tolist()],
            },
        }

        # ROC-AUC if probabilities are available
        if y_prob is not None and len(unique_classes) > 1 and len(set(y_t)) > 1:
            try:
                if len(unique_classes) == 2:
                    y_binary = (y_t == unique_classes[1]).astype(int)
                    pos_probs = y_prob[:, 1] if (y_prob.ndim == 2 and y_prob.shape[1] == 2) else y_prob
                    score = roc_auc_score(y_binary, pos_probs)
                    results["roc_auc_macro"] = round(float(score), 4)
                    results["roc_auc_weighted"] = round(float(score), 4)
                elif y_prob.shape[1] == len(unique_classes):
                    roc_auc_macro = roc_auc_score(
                        y_t,
                        y_prob,
                        labels=unique_classes,
                        multi_class="ovr",
                        average="macro",
                    )
                    roc_auc_weighted = roc_auc_score(
                        y_t,
                        y_prob,
                        labels=unique_classes,
                        multi_class="ovr",
                        average="weighted",
                    )
                    results["roc_auc_macro"] = round(float(roc_auc_macro), 4)
                    results["roc_auc_weighted"] = round(float(roc_auc_weighted), 4)
            except Exception as err:
                logger.debug(f"ROC-AUC calculation skipped or partially defined: {err}")
                results["roc_auc_macro"] = None
                results["roc_auc_weighted"] = None

        return results

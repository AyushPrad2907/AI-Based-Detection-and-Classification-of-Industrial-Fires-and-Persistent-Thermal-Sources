"""
SIH26162 — Model Evaluator and Reporting.

Orchestrates comprehensive model evaluation across test datasets and generates
structured metric reports, markdown summary tables, and confusion matrix outputs.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np
import pandas as pd

from ml.evaluation.metrics import Metrics
from ml.models.base_model import BaseModel

logger = logging.getLogger(__name__)


class Evaluator:
    """
    Orchestrates real model evaluation on held-out test splits.
    """

    def __init__(self, output_dir: Optional[Union[str, Path]] = None):
        self.output_dir = Path(output_dir) if output_dir else Path("ml/evaluation/reports")

    def evaluate_model(
        self,
        model: BaseModel,
        test_data: Any,
        save_report: bool = True,
        report_filename: str = "evaluation_report.json",
    ) -> Dict[str, Any]:
        """
        Run full evaluation on test dataset.

        Args:
            model: Trained BaseModel instance.
            test_data: Test dataset (DataFrame or (X, y) tuple).
            save_report: Whether to save report to disk.
            report_filename: File name for the report JSON.

        Returns:
            Dictionary containing full evaluation metrics.
        """
        metrics = model.evaluate(test_data)

        if save_report:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            report_path = self.output_dir / report_filename
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=2)
            logger.info(f"Evaluation report saved to: {report_path}")

        return metrics

    def generate_markdown_report(self, metrics: Dict[str, Any]) -> str:
        """
        Render a clean markdown table summarizing evaluation metrics.
        """
        lines = [
            "### Model Evaluation Summary",
            "",
            f"- **Test Samples Evaluated**: `{metrics.get('sample_count', 'N/A')}`",
            f"- **Overall Accuracy**: `{metrics.get('accuracy', 'N/A')}`",
            f"- **Macro Precision**: `{metrics.get('precision_macro', 'N/A')}`",
            f"- **Macro Recall**: `{metrics.get('recall_macro', 'N/A')}`",
            f"- **Macro F1-Score**: `{metrics.get('f1_macro', 'N/A')}`",
            f"- **Weighted F1-Score**: `{metrics.get('f1_weighted', 'N/A')}`",
        ]

        if metrics.get("roc_auc_macro") is not None:
            lines.append(f"- **Macro ROC-AUC**: `{metrics.get('roc_auc_macro')}`")

        lines.extend([
            "",
            "#### Per-Class Performance Breakdown",
            "",
            "| Class | Precision | Recall | F1-Score | Support |",
            "|---|---|---|---|---|",
        ])

        per_class = metrics.get("per_class", {})
        for cls_name, vals in per_class.items():
            p = vals.get("precision", 0.0)
            r = vals.get("recall", 0.0)
            f = vals.get("f1_score", 0.0)
            s = vals.get("support", 0)
            lines.append(f"| `{cls_name}` | {p:.4f} | {r:.4f} | {f:.4f} | {s} |")

        lines.extend([
            "",
            "#### Confusion Matrix",
            "",
            f"Classes: `{metrics.get('classes', [])}`",
            "```json",
            json.dumps(metrics.get("confusion_matrix", {}).get("matrix", []), indent=2),
            "```",
        ])

        return "\n".join(lines)

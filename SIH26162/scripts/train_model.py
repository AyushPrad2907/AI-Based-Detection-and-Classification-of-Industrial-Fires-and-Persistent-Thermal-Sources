"""
SIH26162 — ML Model Training and Evaluation CLI.

Trains the Phase 2 Fire & Persistent Thermal Source Classifier using real
processed NASA FIRMS observations, spatio-temporal persistence clustering,
and weak supervision labeling.

Usage:
    python scripts/train_model.py
    python scripts/train_model.py --model-type random_forest --n-estimators 200
    python scripts/train_model.py --evaluate-only
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Ensure repository root and backend in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "backend"))

from ml.evaluation.evaluator import Evaluator
from ml.models.fire_classifier import FireClassifier
from ml.training.trainer import Trainer
from ml.utils.data_utils import FIRMSDatasetLoader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("train_model")


def parse_args():
    parser = argparse.ArgumentParser(description="Train and evaluate SIH26162 ML Classifier.")
    parser.add_argument("--model-type", type=str, default="random_forest", choices=["random_forest", "hist_gradient_boosting"])
    parser.add_argument("--n-estimators", type=int, default=150, help="Number of trees/iterations")
    parser.add_argument("--max-depth", type=int, default=12, help="Max tree depth")
    parser.add_argument("--data-dir", type=str, default="data/processed/firms", help="Path to processed FIRMS CSVs")
    parser.add_argument("--output-dir", type=str, default="ml/saved_models", help="Directory to save model artifacts")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 70)
    print("SIH26162 — Phase 2: AI/ML Pipeline Training & Evaluation")
    print("=" * 70)
    print(f"[*] Model Type:    {args.model_type}")
    print(f"[*] Data Source:   {args.data_dir}")
    print(f"[*] Artifacts:     {args.output_dir}")
    print(f"[*] Random Seed:   {args.seed}")
    print("-" * 70)

    loader = FIRMSDatasetLoader(data_dir=args.data_dir)
    trainer = Trainer(
        data_loader=loader,
        model_type=args.model_type,
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        model_save_dir=args.output_dir,
        random_seed=args.seed,
    )

    results = trainer.train()

    print("=" * 70)
    print("TRAINING & EVALUATION RESULTS")
    print("=" * 70)
    print(f"[+] Total Dataset Size:       {results['dataset_size']} real satellite observations")
    print(f"[+] Training Accuracy:        {results['train_metrics']['train_accuracy'] * 100:.2f}%")
    print(f"[+] Test Accuracy:            {results['test_metrics']['accuracy'] * 100:.2f}%")
    print(f"[+] Test Macro F1-Score:      {results['test_metrics']['f1_macro'] * 100:.2f}%")
    print(f"[+] Test Weighted F1-Score:   {results['test_metrics']['f1_weighted'] * 100:.2f}%")
    if results['test_metrics'].get('roc_auc_macro') is not None:
        print(f"[+] Test Macro ROC-AUC:       {results['test_metrics']['roc_auc_macro']:.4f}")

    print("\n[+] Per-Class Performance:")
    for cls_name, vals in results['test_metrics'].get('per_class', {}).items():
        print(f"    - {cls_name:<24}: Precision={vals['precision']:.3f} | Recall={vals['recall']:.3f} | F1={vals['f1_score']:.3f} (N={vals['support']})")

    print("\n[+] Top 5 Influential Features:")
    for i, (feat, imp) in enumerate(list(results['feature_importances'].items())[:5]):
        print(f"    {i+1}. {feat:<24}: {imp:.4f}")

    print("=" * 70)
    print(f"[+] Model checkpoint saved: {args.output_dir}/fire_classifier.joblib")
    print(f"[+] Clusters saved:         {args.output_dir}/persistent_clusters.json")
    print(f"[+] Metrics report saved:   {args.output_dir}/reports/test_evaluation_report.json")
    print("=" * 70)


if __name__ == "__main__":
    main()

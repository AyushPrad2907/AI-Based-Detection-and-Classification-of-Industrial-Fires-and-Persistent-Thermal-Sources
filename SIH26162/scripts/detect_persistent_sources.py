"""
SIH26162 — Persistent Thermal Source Detection CLI.

Runs spatial-temporal clustering across real NASA FIRMS processed observations
to discover and export persistent industrial thermal anomalies (smelters, flaring units, foundries).

Usage:
    python scripts/detect_persistent_sources.py
    python scripts/detect_persistent_sources.py --min-obs 3 --radius 1500
    python scripts/detect_persistent_sources.py --output data/processed/persistent_sources.json
"""

import argparse
import json
import logging
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "backend"))

from ml.models.thermal_detector import ThermalDetector
from ml.utils.data_utils import FIRMSDatasetLoader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("detect_persistent_sources")


def parse_args():
    parser = argparse.ArgumentParser(description="Discover persistent thermal sources from NASA FIRMS observations.")
    parser.add_argument("--data-dir", type=str, default="data/processed/firms", help="Directory of processed FIRMS CSVs")
    parser.add_argument("--radius", type=float, default=1200.0, help="Spatial clustering radius in meters (eps)")
    parser.add_argument("--min-obs", type=int, default=2, help="Minimum observations to qualify as persistent")
    parser.add_argument("--min-confidence", type=float, default=None, help="Minimum confidence filter (0-100)")
    parser.add_argument("--output", type=str, default="ml/saved_models/persistent_clusters.json", help="Path to save output JSON")
    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 75)
    print("SIH26162 — Persistent Thermal Source Detector (Spatio-Temporal DBSCAN)")
    print("=" * 75)
    print(f"[*] Data Source:         {args.data_dir}")
    print(f"[*] Spatial Radius:      {args.radius} meters")
    print(f"[*] Min Observations:    {args.min_obs}")
    print("-" * 75)

    loader = FIRMSDatasetLoader(data_dir=args.data_dir)
    df = loader.load_dataset(min_confidence=args.min_confidence)

    if df.empty:
        print("[!] No observations found in data directory.")
        return

    print(f"[+] Loaded {len(df)} real satellite observations.")

    detector = ThermalDetector(
        spatial_eps_meters=args.radius,
        min_samples=2,
        min_persistence_observations=args.min_obs,
    )

    df_clustered, clusters = detector.fit_predict_clusters(df)
    persistent_clusters = [c for c in clusters if c.is_persistent]

    print("\n" + "=" * 75)
    print("CLUSTERING & PERSISTENCE SUMMARY")
    print("=" * 75)
    print(f"[+] Total Observations Analyzed:  {len(df)}")
    print(f"[+] Clustered Detections:         {(df_clustered['cluster_id'] != -1).sum()}")
    print(f"[+] Isolated/Noise Detections:    {(df_clustered['cluster_id'] == -1).sum()}")
    print(f"[+] Total Spatial Clusters Found: {len(clusters)}")
    print(f"[+] Persistent Thermal Sources:   {len(persistent_clusters)}")
    print("-" * 75)

    if persistent_clusters:
        print("\nTop Persistent Thermal Sources Discovered:")
        for idx, c in enumerate(sorted(persistent_clusters, key=lambda x: x.observation_count, reverse=True)[:10]):
            print(
                f"  [{idx+1}] Cluster #{c.cluster_id:03d} | Centroid: ({c.centroid_lat:.4f}, {c.centroid_lon:.4f}) | "
                f"Passes: {c.observation_count:<2} | Span: {c.duration_days:.1f}d | "
                f"Mean FRP: {c.mean_frp:5.1f} MW | Max FRP: {c.max_frp:5.1f} MW | Night: {c.night_ratio*100:4.0f}%"
            )

    detector.save(args.output)
    print("=" * 75)
    print(f"[+] Discovered persistent sources saved to: {args.output}")
    print("=" * 75)


if __name__ == "__main__":
    main()

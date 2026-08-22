"""
SIH26162 — NASA FIRMS Data Ingestion Script.

Downloads REAL active fire and thermal anomaly observations from the
official NASA FIRMS API and saves raw data under data/raw/firms/.
Optionally triggers the preprocessing pipeline.

Usage:
    # 1. Download India 1-day VIIRS active fires:
    python scripts/download_firms_data.py --country IND --days 1 --source VIIRS_SNPP_NRT

    # 2. Download and preprocess in one step:
    python scripts/download_firms_data.py --country IND --days 1 --preprocess

    # 3. Download using a custom bounding box (West, South, East, North):
    python scripts/download_firms_data.py --bbox 68.0,6.0,97.0,37.0 --days 1

Prerequisites:
    Set FIRMS_API_KEY in your .env file or environment, or pass --api-key.
    Get a free API key at: https://firms.modaps.eosdis.nasa.gov/api/area/
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Ensure repository root and backend are in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "backend"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(REPO_ROOT / ".env")

from app.config import settings
from app.services.firms_service import (
    FIRMSAuthenticationError,
    FIRMSException,
    FIRMSQuotaExceededError,
    FIRMSService,
    FIRMSValidationError,
    VALID_SOURCES,
)
from ml.preprocessing.firms_preprocessor import FIRMSPreprocessor


def parse_arguments() -> argparse.Namespace:
    """Parse and validate command line arguments."""
    parser = argparse.ArgumentParser(
        description="Download real active fire/thermal data from the official NASA FIRMS API."
    )

    # API & Source
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="NASA FIRMS MAP_KEY (defaults to FIRMS_API_KEY environment variable)",
    )
    parser.add_argument(
        "--source",
        type=str,
        default="VIIRS_SNPP_NRT",
        choices=list(VALID_SOURCES),
        help="Satellite data source (default: VIIRS_SNPP_NRT)",
    )

    # Geographic Scope (Country or Bounding Box)
    parser.add_argument(
        "--country",
        type=str,
        default=None,
        help="ISO 3166-1 alpha-3 country code (e.g., 'IND'). Used if --bbox is not provided.",
    )
    parser.add_argument(
        "--bbox",
        type=str,
        default=None,
        help="Geographic bounding box: 'min_lon,min_lat,max_lon,max_lat' (e.g. '68.0,6.0,97.0,37.0')",
    )

    # Time Scope
    parser.add_argument(
        "--days",
        type=int,
        default=1,
        choices=list(range(1, 11)),
        help="Number of days to fetch (1 to 10, default: 1)",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Target date in ISO format YYYY-MM-DD (optional, defaults to current NRT data)",
    )

    # Storage & Pipeline
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Destination path for raw CSV (default: data/raw/firms/firms_<source>_<target>_<timestamp>.csv)",
    )
    parser.add_argument(
        "--preprocess",
        action="store_true",
        help="Run preprocessing immediately on the downloaded data",
    )
    parser.add_argument(
        "--processed-output",
        type=str,
        default=None,
        help="Destination path for processed data (default: data/processed/firms/...)",
    )
    parser.add_argument(
        "--min-confidence",
        type=str,
        default=None,
        help="Minimum confidence filter for preprocessing ('low', 'nominal', 'high', or 0-100)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable detailed debug logging",
    )

    return parser.parse_args()


def parse_bbox_str(bbox_str: str) -> List[float]:
    """Parse comma-separated bounding box string."""
    try:
        parts = [float(p.strip()) for p in bbox_str.split(",")]
        if len(parts) != 4:
            raise ValueError("Must have 4 coordinates")
        return parts
    except Exception as err:
        raise ValueError(
            f"Invalid --bbox argument '{bbox_str}'. Expected format: min_lon,min_lat,max_lon,max_lat (e.g. 68.0,6.0,97.0,37.0)"
        ) from err


def main() -> int:
    """Main CLI execution routine."""
    args = parse_arguments()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger("FIRMSDownloader")

    # Determine API key
    api_key = args.api_key or os.getenv("FIRMS_API_KEY") or settings.firms_api_key
    if not api_key or not api_key.strip():
        logger.error(
            "Missing NASA FIRMS API key! Please set FIRMS_API_KEY in your .env file or pass --api-key <KEY>."
        )
        logger.error("Get a free MAP_KEY at: https://firms.modaps.eosdis.nasa.gov/api/area/")
        return 1

    firms_service = FIRMSService(api_key=api_key)

    # Determine target & filenames
    timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    target_tag = ""

    print("=" * 70)
    print("SIH26162 — NASA FIRMS Active Fire Data Ingestion")
    print("=" * 70)

    try:
        if args.bbox:
            bbox_coords = parse_bbox_str(args.bbox)
            target_tag = f"bbox_{bbox_coords[0]}_{bbox_coords[1]}_{bbox_coords[2]}_{bbox_coords[3]}"
            print(f"[*] Query Mode:  Area Bounding Box ({bbox_coords})")
            print(f"[*] Source:      {args.source}")
            print(f"[*] Days Range:  {args.days} day(s)")
            if args.date:
                print(f"[*] Target Date: {args.date}")
            print(f"[*] Fetching real NASA FIRMS data...")

            raw_csv = firms_service.fetch_area_fires_sync(
                bbox=bbox_coords,
                source=args.source,
                days=args.days,
                target_date=args.date,
            )
        else:
            country = (args.country or settings.firms_default_country or "IND").upper()
            target_tag = f"country_{country}"
            print(f"[*] Query Mode:  Country ({country})")
            print(f"[*] Source:      {args.source}")
            print(f"[*] Days Range:  {args.days} day(s)")
            if args.date:
                print(f"[*] Target Date: {args.date}")
            print(f"[*] Fetching real NASA FIRMS data...")

            raw_csv = firms_service.fetch_country_fires_sync(
                country=country,
                source=args.source,
                days=args.days,
                target_date=args.date,
            )

        # Parse records count
        records = firms_service.parse_csv_response(raw_csv)
        record_count = len(records)
        print(f"[+] Download successful! Received {record_count} fire observations.")

        # Determine raw output path
        raw_dir = REPO_ROOT / "data" / "raw" / "firms"
        raw_dir.mkdir(parents=True, exist_ok=True)

        if args.output:
            raw_output_path = Path(args.output)
            raw_output_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            raw_filename = f"firms_{args.source}_{target_tag}_{timestamp_str}.csv"
            raw_output_path = raw_dir / raw_filename

        with open(raw_output_path, "w", encoding="utf-8", newline="") as f:
            f.write(raw_csv)

        file_size_kb = raw_output_path.stat().st_size / 1024.0
        print(f"[+] Raw data saved:  {raw_output_path} ({file_size_kb:.1f} KB)")

        # Optional Preprocessing Step
        if args.preprocess:
            print("-" * 70)
            print("[*] Running Preprocessing Pipeline...")
            preprocessor = FIRMSPreprocessor(
                min_confidence=args.min_confidence,
            )

            proc_dir = REPO_ROOT / "data" / "processed" / "firms"
            proc_dir.mkdir(parents=True, exist_ok=True)

            if args.processed_output:
                proc_output_path = Path(args.processed_output)
            else:
                proc_filename = f"firms_{args.source}_{target_tag}_{timestamp_str}_processed.csv"
                proc_output_path = proc_dir / proc_filename

            processed_df = preprocessor.preprocess(
                source=raw_output_path,
                output_path=proc_output_path,
            )
            print(f"[+] Preprocessing completed!")
            print(f"[+] Clean records:   {len(processed_df)}")
            print(f"[+] Processed data:  {proc_output_path}")

        print("=" * 70)
        return 0

    except FIRMSAuthenticationError as err:
        logger.error(f"Authentication Failure: {err}")
        return 1
    except FIRMSValidationError as err:
        logger.error(f"Parameter Validation Failure: {err}")
        return 1
    except FIRMSQuotaExceededError as err:
        logger.error(f"API Limit / Quota Exceeded: {err}")
        return 1
    except FIRMSException as err:
        logger.error(f"FIRMS Error: {err}")
        return 1
    except Exception as err:
        logger.exception(f"Unexpected execution error: {err}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

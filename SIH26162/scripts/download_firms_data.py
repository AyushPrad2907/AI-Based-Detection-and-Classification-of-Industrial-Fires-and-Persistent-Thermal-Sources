"""
SIH26162 — Download NASA FIRMS Data (Placeholder).

This script will automate downloading active fire data from
the NASA FIRMS API. Requires a FIRMS MAP_KEY.

Usage:
    python scripts/download_firms_data.py --country IND --days 10

NOT YET IMPLEMENTED — will be completed in Phase 1.
"""

import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Download NASA FIRMS active fire data."
    )
    parser.add_argument(
        "--country", type=str, default="IND",
        help="ISO 3166-1 alpha-3 country code (default: IND)"
    )
    parser.add_argument(
        "--days", type=int, default=1, choices=[1, 2, 10],
        help="Number of days of data to fetch (default: 1)"
    )
    parser.add_argument(
        "--output", type=str, default="data/raw/firms_data.csv",
        help="Output file path (default: data/raw/firms_data.csv)"
    )
    parser.add_argument(
        "--source", type=str, default="VIIRS_SNPP_NRT",
        choices=["VIIRS_SNPP_NRT", "MODIS_NRT"],
        help="FIRMS data source (default: VIIRS_SNPP_NRT)"
    )

    args = parser.parse_args()

    print(f"[INFO] This script will download FIRMS data:")
    print(f"  Country: {args.country}")
    print(f"  Days:    {args.days}")
    print(f"  Source:  {args.source}")
    print(f"  Output:  {args.output}")
    print()
    print("[!] NOT YET IMPLEMENTED — will be completed in Phase 1.")
    print("[!] You need a FIRMS_API_KEY in your .env file.")
    print("[!] Get one at: https://firms.modaps.eosdis.nasa.gov/api/area/")


if __name__ == "__main__":
    main()

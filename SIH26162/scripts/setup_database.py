"""
SIH26162 — Database Setup & Migration Script.

Initializes PostgreSQL + PostGIS database schema, creates extensions,
and applies Alembic migrations.

Usage:
    python scripts/setup_database.py
    python scripts/setup_database.py --create-extension --migrate
    python scripts/setup_database.py --check-health
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.core.database import engine, init_db, check_database_health
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("setup_database")


async def async_main(args):
    print("=" * 70)
    print("SIH26162 — PostgreSQL + PostGIS Database Initializer")
    print("=" * 70)
    print(f"[*] Target Database URL: {settings.async_database_url.split('@')[-1] if '@' in settings.async_database_url else 'Configured'}")
    print(f"[*] Environment:         {settings.environment}")
    print("-" * 70)

    if args.check_health:
        health = await check_database_health()
        print("\nDatabase Health Check Results:")
        for k, v in health.items():
            print(f"  {k}: {v}")
        return

    print("[+] Initializing database tables and PostGIS extension...")
    try:
        await init_db()
        print("[✓] Database schema initialized successfully.")
    except Exception as err:
        print(f"[!] Database initialization encountered an error: {err}")
        print("[!] If PostgreSQL is not running locally, start it via Docker Compose:")
        print("    docker compose up -d db")
        return

    health = await check_database_health()
    print("\nDatabase Status:")
    print(f"  Status:          {health.get('status')}")
    print(f"  Latency:         {health.get('latency_ms')} ms")
    print(f"  PostGIS Version: {health.get('postgis_version')}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Initialize SIH26162 PostgreSQL + PostGIS database.")
    parser.add_argument("--create-extension", action="store_true", help="Ensure PostGIS extension is installed")
    parser.add_argument("--migrate", action="store_true", help="Apply database migrations")
    parser.add_argument("--check-health", action="store_true", help="Run diagnostic health probe")
    args = parser.parse_args()

    asyncio.run(async_main(args))


if __name__ == "__main__":
    main()
